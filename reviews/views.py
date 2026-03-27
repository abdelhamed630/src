from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count
from django.utils import timezone

from .models import Review, ReviewHelpful
from .serializers import ReviewSerializer, CreateReviewSerializer, SellerReplySerializer


class ProductReviewListView(APIView):
    """
    GET  /reviews/products/<slug>/   — list reviews for a product
    POST /reviews/products/<slug>/   — buyer submits a review (must have purchased)
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, slug):
        from products.models import Product
        product = get_object_or_404(Product, slug=slug, is_active=True)
        reviews = product.reviews.select_related('buyer').order_by('-created_at')

        # Rating summary
        agg = reviews.aggregate(avg=Avg('rating'), total=Count('id'))
        stars = {str(i): reviews.filter(rating=i).count() for i in range(1, 6)}

        return Response({
            'summary': {
                'average_rating': round(agg['avg'] or 0, 1),
                'total_reviews' : agg['total'],
                'stars'         : stars,
            },
            'reviews': ReviewSerializer(reviews, many=True, context={'request': request}).data,
        })

    def post(self, request, slug):
        from products.models import Product
        from orders.models import OrderItem

        product = get_object_or_404(Product, slug=slug, is_active=True)

        # Check if already reviewed
        if Review.objects.filter(product=product, buyer=request.user).exists():
            return Response({'detail': 'You have already reviewed this product.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check verified purchase
        order_item = OrderItem.objects.filter(
            order__buyer=request.user,
            product=product,
            item_status='delivered',
        ).first()

        serializer = CreateReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = serializer.save(
            product=product,
            buyer=request.user,
            order_item=order_item,
            is_verified_purchase=bool(order_item),
        )

        # Update product rating cache on SellerProfile
        self._update_seller_rating(product)

        return Response(ReviewSerializer(review, context={'request': request}).data, status=status.HTTP_201_CREATED)

    def _update_seller_rating(self, product):
        try:
            if product.seller:
                profile = product.seller.seller_profile
                agg = Review.objects.filter(product__seller=product.seller).aggregate(
                    avg=Avg('rating'), total=Count('id')
                )
                profile.rating = round(agg['avg'] or 0, 2)
                profile.reviews_count = agg['total']
                profile.save(update_fields=['rating', 'reviews_count'])
        except Exception:
            pass


class ReviewDetailView(APIView):
    """
    PATCH  /reviews/<id>/  — buyer edits own review
    DELETE /reviews/<id>/  — buyer deletes own review
    """
    permission_classes = [IsAuthenticated]

    def _get_review(self, pk, user):
        return get_object_or_404(Review, id=pk, buyer=user)

    def patch(self, request, pk):
        review = self._get_review(pk, request.user)
        serializer = CreateReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReviewSerializer(review, context={'request': request}).data)

    def delete(self, request, pk):
        self._get_review(pk, request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SellerReplyView(APIView):
    """POST /reviews/<id>/reply/ — seller replies to a review on their product"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_seller:
            return Response({'detail': 'Seller access required.'}, status=status.HTTP_403_FORBIDDEN)

        review = get_object_or_404(Review, id=pk, product__seller=request.user)
        serializer = SellerReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review.seller_reply    = serializer.validated_data['seller_reply']
        review.seller_reply_at = timezone.now()
        review.save(update_fields=['seller_reply', 'seller_reply_at'])

        return Response(ReviewSerializer(review, context={'request': request}).data)


class MarkReviewHelpfulView(APIView):
    """POST /reviews/<id>/helpful/ — toggle helpful vote"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        review = get_object_or_404(Review, id=pk)
        obj, created = ReviewHelpful.objects.get_or_create(review=review, user=request.user)
        if not created:
            obj.delete()
            review.helpful_count = max(0, review.helpful_count - 1)
            action = 'removed'
        else:
            review.helpful_count += 1
            action = 'added'
        review.save(update_fields=['helpful_count'])
        return Response({'action': action, 'helpful_count': review.helpful_count})
