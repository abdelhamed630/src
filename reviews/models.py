from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """
    Only buyers who actually purchased the product can review it.
    One review per (buyer, product) pair.
    """
    product    = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    buyer      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    order_item = models.OneToOneField('orders.OrderItem', on_delete=models.SET_NULL, null=True, blank=True)

    rating     = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title      = models.CharField(max_length=100, blank=True)
    body       = models.TextField(blank=True)

    # Seller can reply once
    seller_reply     = models.TextField(blank=True)
    seller_reply_at  = models.DateTimeField(null=True, blank=True)

    is_verified_purchase = models.BooleanField(default=False)
    helpful_count        = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'buyer')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.buyer.email} → {self.product.name} ({self.rating}★)'


class ReviewHelpful(models.Model):
    """Track who marked a review as helpful (no duplicates)."""
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('review', 'user')
