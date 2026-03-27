from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from products.models import Product
from products.serializers import ProductListSerializer
from .models import WishlistItem


class WishlistView(APIView):
    """GET /wishlist/ — list all wishlist items"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items    = WishlistItem.objects.filter(user=request.user).select_related('product').prefetch_related('product__images')
        products = [item.product for item in items]
        data     = ProductListSerializer(products, many=True, context={'request': request}).data
        # add added_at to each
        at_map = {item.product_id: item.added_at for item in items}
        for d, product in zip(data, products):
            d['added_at'] = at_map[product.id]
        return Response(data)


class WishlistToggleView(APIView):
    """
    POST /wishlist/<slug>/ — add if not in wishlist, remove if already there
    Returns: { "action": "added"|"removed", "in_wishlist": true|false }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug, is_active=True)
        item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()
            return Response({'action': 'removed', 'in_wishlist': False})
        return Response({'action': 'added', 'in_wishlist': True}, status=status.HTTP_201_CREATED)


class WishlistCheckView(APIView):
    """GET /wishlist/check/<slug>/ — check if product is in wishlist"""
    permission_classes = [IsAuthenticated]

    def get(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        in_wishlist = WishlistItem.objects.filter(user=request.user, product=product).exists()
        return Response({'in_wishlist': in_wishlist})
