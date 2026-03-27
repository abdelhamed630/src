from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Cart, CartItem, Coupon
from .serializers import (
    CartSerializer, AddToCartSerializer,
    UpdateCartItemSerializer, ApplyCouponSerializer,
)


def get_or_create_cart(user) -> Cart:
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


# ── GET /cart/  ───────────────────────────────────────────────────────
class CartView(APIView):
    """
    GET  /cart/  → عرض الكارت كاملة
    DELETE /cart/ → مسح الكارت كلها
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)

        # لو الكارت منتهية، امسحها وابدأ جديدة
        if cart.is_expired:
            cart.items.all().delete()
            cart.coupon = None
            cart.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        cart.coupon = None
        cart.save()
        return Response({'detail': 'Cart cleared.'}, status=status.HTTP_200_OK)


# ── POST /cart/add/  ──────────────────────────────────────────────────
class AddToCartView(APIView):
    """
    POST /cart/add/
    { "variant_id": 1, "quantity": 2 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant  = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']

        cart = get_or_create_cart(request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart, variant=variant,
            defaults={'quantity': quantity, 'saved_for_later': False}
        )

        if not created:
            # المنتج موجود — نزود الكمية
            new_qty = item.quantity + quantity
            if new_qty > CartItem.MAX_QUANTITY:
                return Response(
                    {'detail': f'Maximum quantity per item is {CartItem.MAX_QUANTITY}.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_qty > variant.stock:
                return Response(
                    {'detail': f'Only {variant.stock} items available in stock.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.quantity       = new_qty
            item.saved_for_later = False  # لو كان saved، يرجع للكارت
            item.save()

        # تحديث الكارت عشان يتجدد الـ updated_at (يمدد الـ expiry)
        cart.save()

        return Response(
            CartSerializer(cart, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )


# ── PATCH /cart/items/<id>/  ──────────────────────────────────────────
class UpdateCartItemView(APIView):
    """
    PATCH /cart/items/<id>/
    { "quantity": 3 }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)

        serializer = UpdateCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_qty = serializer.validated_data['quantity']

        if new_qty > item.variant.stock:
            return Response(
                {'detail': f'Only {item.variant.stock} items available in stock.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.quantity = new_qty
        item.save()
        cart.save()

        return Response(CartSerializer(cart, context={'request': request}).data)


# ── DELETE /cart/items/<id>/  ─────────────────────────────────────────
class RemoveCartItemView(APIView):
    """DELETE /cart/items/<id>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, item_id):
        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        cart.save()
        return Response(CartSerializer(cart, context={'request': request}).data)


# ── POST /cart/items/<id>/save-for-later/  ────────────────────────────
class SaveForLaterView(APIView):
    """
    POST /cart/items/<id>/save-for-later/  → ينقل من الكارت لـ Saved
    POST /cart/items/<id>/move-to-cart/    → ينقل من Saved للكارت
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, item_id, action):
        cart = get_or_create_cart(request.user)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if action == 'save':
            item.saved_for_later = True
        elif action == 'move':
            # تحقق من الـ stock قبل الرجوع للكارت
            if item.variant.stock < item.quantity:
                return Response(
                    {'detail': f'Only {item.variant.stock} items available in stock.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.saved_for_later = False
        else:
            return Response({'detail': 'Invalid action.'}, status=status.HTTP_400_BAD_REQUEST)

        item.save()
        cart.save()
        return Response(CartSerializer(cart, context={'request': request}).data)


# ── POST /cart/coupon/  ───────────────────────────────────────────────
class ApplyCouponView(APIView):
    """
    POST /cart/coupon/   → تطبيق كود خصم
    DELETE /cart/coupon/ → إزالة كود الخصم
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ApplyCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code'].upper().strip()

        cart = get_or_create_cart(request.user)

        try:
            coupon = Coupon.objects.get(code=code)
        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code.'}, status=status.HTTP_400_BAD_REQUEST)

        valid, reason = coupon.is_valid(cart.subtotal)
        if not valid:
            return Response({'detail': reason}, status=status.HTTP_400_BAD_REQUEST)

        cart.coupon = coupon
        cart.save()

        return Response({
            'detail'         : 'Coupon applied successfully.',
            'discount_amount': str(cart.discount_amount),
            'total'          : str(cart.total),
        })

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.coupon = None
        cart.save()
        return Response({'detail': 'Coupon removed.'})


# ── GET /cart/summary/  ───────────────────────────────────────────────
class CartSummaryView(APIView):
    """
    GET /cart/summary/
    نسخة خفيفة للـ header (عدد الأيتمز والتوتال بس)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        return Response({
            'total_items'    : cart.total_items,
            'subtotal'       : str(cart.subtotal),
            'discount_amount': str(cart.discount_amount),
            'total'          : str(cart.total),
            'coupon_code'    : cart.coupon.code if cart.coupon else None,
            'is_expired'     : cart.is_expired,
        })
