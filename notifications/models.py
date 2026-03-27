from django.db import models
from django.conf import settings


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_PLACED    = 'order_placed',    'Order Placed'
        ORDER_CONFIRMED = 'order_confirmed', 'Order Confirmed'
        ORDER_SHIPPED   = 'order_shipped',   'Order Shipped'
        ORDER_DELIVERED = 'order_delivered', 'Order Delivered'
        ORDER_CANCELLED = 'order_cancelled', 'Order Cancelled'
        NEW_MESSAGE     = 'new_message',     'New Message'
        NEW_REVIEW      = 'new_review',      'New Review'
        SELLER_APPROVED = 'seller_approved', 'Seller Approved'
        SELLER_REJECTED = 'seller_rejected', 'Seller Rejected'
        PROMO           = 'promo',           'Promotion'

    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    type       = models.CharField(max_length=30, choices=Type.choices)
    title      = models.CharField(max_length=200)
    body       = models.TextField()
    link       = models.CharField(max_length=300, blank=True)  # frontend route
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.user.email}: {self.title}'

    @classmethod
    def send(cls, user, type, title, body, link=''):
        return cls.objects.create(user=user, type=type, title=title, body=body, link=link)
