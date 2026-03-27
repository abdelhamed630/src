import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending Payment'
        CONFIRMED  = 'confirmed',  'Confirmed'
        PROCESSING = 'processing', 'Processing'
        SHIPPED    = 'shipped',    'Shipped'
        DELIVERED  = 'delivered',  'Delivered'
        CANCELLED  = 'cancelled',  'Cancelled'
        REFUNDED   = 'refunded',   'Refunded'

    class PaymentMethod(models.TextChoices):
        COD         = 'cod',         'Cash on Delivery'
        CREDIT_CARD = 'credit_card', 'Credit Card'
        INSTAPAY    = 'instapay',    'InstaPay'
        VODAFONE    = 'vodafone',    'Vodafone Cash'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number   = models.CharField(max_length=20, unique=True, blank=True)
    buyer          = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')

    # Snapshot of shipping address
    shipping_name     = models.CharField(max_length=255)
    shipping_phone    = models.CharField(max_length=20)
    shipping_address1 = models.CharField(max_length=255)
    shipping_address2 = models.CharField(max_length=255, blank=True)
    shipping_city     = models.CharField(max_length=100)
    shipping_state    = models.CharField(max_length=100, blank=True)
    shipping_postal   = models.CharField(max_length=20, blank=True)
    shipping_country  = models.CharField(max_length=100, default='Egypt')

    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method  = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    payment_status  = models.CharField(
        max_length=20,
        choices=[('unpaid','Unpaid'),('paid','Paid'),('refunded','Refunded')],
        default='unpaid'
    )

    subtotal        = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost   = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total           = models.DecimalField(max_digits=12, decimal_places=2)

    coupon_code     = models.CharField(max_length=50, blank=True)
    notes           = models.TextField(blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    confirmed_at    = models.DateTimeField(null=True, blank=True)
    shipped_at      = models.DateTimeField(null=True, blank=True)
    delivered_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.order_number} — {self.buyer.email}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            import random, string
            self.order_number = 'ORD-' + ''.join(random.choices(string.digits, k=8))
        super().save(*args, **kwargs)

    @property
    def full_shipping_address(self):
        parts = [self.shipping_address1]
        if self.shipping_address2:
            parts.append(self.shipping_address2)
        parts += [self.shipping_city, self.shipping_country]
        return ', '.join(parts)


class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    seller       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sold_items')

    # Snapshots — never change even if product is updated/deleted
    product_name = models.CharField(max_length=255)
    product_slug = models.CharField(max_length=255, blank=True)
    variant_sku  = models.CharField(max_length=100, blank=True)
    variant_attrs = models.JSONField(default=dict)  # {"Color": "Red", "Size": "XL"}
    product_image = models.URLField(blank=True)

    # Live FK (nullable in case product deleted)
    product      = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    variant      = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)

    quantity     = models.PositiveSmallIntegerField()
    unit_price   = models.DecimalField(max_digits=10, decimal_places=2)
    total_price  = models.DecimalField(max_digits=12, decimal_places=2)

    # Per-item seller fulfilment status
    item_status  = models.CharField(
        max_length=20,
        choices=[
            ('pending','Pending'), ('processing','Processing'),
            ('shipped','Shipped'), ('delivered','Delivered'), ('cancelled','Cancelled')
        ],
        default='pending'
    )
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at      = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.quantity}x {self.product_name} in Order #{self.order.order_number}'


class OrderStatusLog(models.Model):
    """Audit trail for every status change."""
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_logs')
    from_status = models.CharField(max_length=20, blank=True)
    to_status   = models.CharField(max_length=20)
    changed_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    note        = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
