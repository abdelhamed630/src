from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction

from .models import Order, OrderItem, OrderStatusLog
from .serializers import (
    OrderSerializer, PlaceOrderSerializer,
    UpdateOrderItemStatusSerializer, SellerOrderItemSerializer,
)
from accounts.models import Address
from cart.models import Cart


# ── Buyer: Place Order ────────────────────────────────────────────────
class PlaceOrderView(APIView):
    """
    POST /orders/place/
    Converts cart → order. Requires a saved address.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        address = get_object_or_404(Address, id=serializer.validated_data['address_id'], user=user)

        try:
            cart = user.cart
        except Cart.DoesNotExist:
            return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        active_items = list(cart.active_items)
        if not active_items:
            return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate all items are still available
        for item in active_items:
            if not item.is_available:
                return Response(
                    {'detail': f'"{item.variant.product.name}" is no longer available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        order = Order.objects.create(
            buyer             = user,
            shipping_name     = address.full_name,
            shipping_phone    = address.phone,
            shipping_address1 = address.address_line1,
            shipping_address2 = address.address_line2,
            shipping_city     = address.city,
            shipping_state    = address.state,
            shipping_postal   = address.postal_code,
            shipping_country  = address.country,
            payment_method    = serializer.validated_data['payment_method'],
            notes             = serializer.validated_data.get('notes', ''),
            subtotal          = cart.subtotal,
            discount_amount   = cart.discount_amount,
            shipping_cost     = 0,
            total             = cart.total,
            coupon_code       = cart.coupon.code if cart.coupon else '',
        )

        for item in active_items:
            product = item.variant.product
            # Get seller — fall back to admin if product has no seller
            seller_profile = getattr(product, 'seller', None)
            seller = seller_profile.user if seller_profile else user

            # Get image URL
            img = product.images.filter(is_primary=True).first() or product.images.first()
            img_url = request.build_absolute_uri(img.image.url) if img else ''

            OrderItem.objects.create(
                order         = order,
                seller        = seller,
                product       = product,
                variant       = item.variant,
                product_name  = product.name,
                product_slug  = product.slug,
                variant_sku   = item.variant.sku,
                variant_attrs = {
                    av.attribute.name: av.value
                    for av in item.variant.attribute_values.select_related('attribute').all()
                },
                product_image = img_url,
                quantity      = item.quantity,
                unit_price    = item.unit_price,
                total_price   = item.total_price,
            )

            # Reduce stock
            item.variant.stock -= item.quantity
            item.variant.save(update_fields=['stock'])

        # Clear cart
        cart.items.all().delete()
        cart.coupon = None
        cart.save()

        # Log status
        OrderStatusLog.objects.create(order=order, to_status='pending', changed_by=user)

        # Send confirmation email async (Celery)
        try:
            from .tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(str(order.id))
        except Exception:
            pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


# ── Buyer: List My Orders ─────────────────────────────────────────────
class BuyerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = (
            Order.objects
            .filter(buyer=request.user)
            .prefetch_related('items', 'status_logs')
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


# ── Buyer: Order Detail ───────────────────────────────────────────────
class BuyerOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = get_object_or_404(
            Order.objects.prefetch_related('items', 'status_logs'),
            order_number=order_number, buyer=request.user
        )
        return Response(OrderSerializer(order).data)

    def delete(self, request, order_number):
        """Cancel order if still pending"""
        order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
        if order.status not in ('pending', 'confirmed'):
            return Response(
                {'detail': 'Cannot cancel order at this stage.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        old_status = order.status
        order.status = 'cancelled'
        order.save()
        # Restore stock
        for item in order.items.select_related('variant'):
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save(update_fields=['stock'])
        OrderStatusLog.objects.create(order=order, from_status=old_status, to_status='cancelled', changed_by=request.user)
        return Response({'detail': 'Order cancelled successfully.'})


# ── Buyer: Download Invoice PDF ───────────────────────────────────────
class DownloadInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        from .pdf_utils import generate_invoice_pdf
        order = get_object_or_404(
            Order.objects.prefetch_related('items'),
            order_number=order_number, buyer=request.user
        )
        pdf_buffer = generate_invoice_pdf(order)
        from django.http import FileResponse
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=f'invoice_{order.order_number}.pdf',
            content_type='application/pdf'
        )


# ── Seller: List Incoming Orders ──────────────────────────────────────
class SellerOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)

        items = (
            OrderItem.objects
            .filter(seller=request.user)
            .select_related('order', 'order__buyer')
            .order_by('-order__created_at')
        )

        # Filter by status
        item_status = request.query_params.get('status')
        if item_status:
            items = items.filter(item_status=item_status)

        serializer = SellerOrderItemSerializer(items, many=True)
        return Response(serializer.data)


# ── Seller: Update Item Status ────────────────────────────────────────
class SellerUpdateOrderItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, item_id):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)

        item = get_object_or_404(OrderItem, id=item_id, seller=request.user)
        serializer = UpdateOrderItemStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item.item_status = serializer.validated_data['item_status']
        if serializer.validated_data.get('tracking_number'):
            item.tracking_number = serializer.validated_data['tracking_number']
        if item.item_status == 'shipped':
            item.shipped_at = timezone.now()
        item.save()

        return Response(SellerOrderItemSerializer(item).data)


# ── Seller: Download Buyer Invoice ────────────────────────────────────
class SellerDownloadInvoiceView(APIView):
    """Seller downloads the invoice for a specific order item (their sale)"""
    permission_classes = [IsAuthenticated]

    def get(self, request, item_id):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)

        from .pdf_utils import generate_invoice_pdf
        item = get_object_or_404(OrderItem, id=item_id, seller=request.user)
        order = item.order
        pdf_buffer = generate_invoice_pdf(order, seller_filter=request.user)
        from django.http import FileResponse
        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=f'invoice_{order.order_number}.pdf',
            content_type='application/pdf'
        )


# ── Seller: Dashboard Stats ───────────────────────────────────────────
class SellerDashboardView(APIView):
    """
    GET /orders/seller/dashboard/
    Returns aggregate stats for the seller's dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Sum, Count, Avg
        from django.utils import timezone
        from datetime import timedelta

        items = OrderItem.objects.filter(seller=request.user)

        # All-time stats
        all_time = items.aggregate(
            total_revenue = Sum('total_price'),
            total_orders  = Count('order', distinct=True),
            total_units   = Sum('quantity'),
        )

        # This month
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        this_month  = items.filter(order__created_at__gte=month_start).aggregate(
            revenue = Sum('total_price'),
            orders  = Count('order', distinct=True),
        )

        # Last 30 days daily revenue
        daily = []
        for i in range(29, -1, -1):
            day   = timezone.now().date() - timedelta(days=i)
            rev   = items.filter(order__created_at__date=day).aggregate(r=Sum('total_price'))['r'] or 0
            daily.append({'date': str(day), 'revenue': float(rev)})

        # Pending items
        pending_count = items.filter(item_status='pending').count()

        # Top products
        top_products = (
            items
            .values('product_name')
            .annotate(units=Sum('quantity'), revenue=Sum('total_price'))
            .order_by('-revenue')[:5]
        )

        return Response({
            'all_time': {
                'revenue'      : float(all_time['total_revenue'] or 0),
                'orders'       : all_time['total_orders'] or 0,
                'units_sold'   : all_time['total_units'] or 0,
            },
            'this_month': {
                'revenue': float(this_month['revenue'] or 0),
                'orders' : this_month['orders'] or 0,
            },
            'pending_orders'  : pending_count,
            'daily_revenue'   : daily,
            'top_products'    : list(top_products),
        })


# ── Admin Order List ───────────────────────────────────────────────────
class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'detail': 'Forbidden.'}, status=403)
        from .models import Order
        from .serializers import OrderSerializer
        orders = Order.objects.select_related('buyer').prefetch_related('items').order_by('-created_at')
        data = [{
            'id': str(o.id),
            'order_number': o.order_number,
            'buyer': {
                'id': o.buyer.id,
                'email': o.buyer.email,
                'full_name': o.buyer.full_name,
            },
            'status': o.status,
            'total_price': str(o.total_price),
            'items': [{'id': i.id, 'product_name': i.product_name, 'quantity': i.quantity} for i in o.items.all()],
            'created_at': o.created_at,
        } for o in orders]
        return Response({'results': data, 'count': len(data)})
