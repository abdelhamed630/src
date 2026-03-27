from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


# ── Coupon ────────────────────────────────────────────────────────────
class Coupon(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED      = 'fixed',      'Fixed Amount'

    code            = models.CharField(max_length=50, unique=True)
    discount_type   = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    discount_value  = models.DecimalField(max_digits=10, decimal_places=2)  # % أو مبلغ ثابت
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # أقل حد للطلب
    max_uses        = models.PositiveIntegerField(null=True, blank=True)     # أقصى عدد استخدامات (None = غير محدود)
    used_count      = models.PositiveIntegerField(default=0)
    is_active       = models.BooleanField(default=True)
    expires_at      = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.code} ({self.discount_type}: {self.discount_value})'

    def is_valid(self, order_total: Decimal) -> tuple[bool, str]:
        """بترجع (True, '') أو (False, 'سبب الرفض')"""
        if not self.is_active:
            return False, 'Coupon is not active.'
        if self.expires_at and timezone.now() > self.expires_at:
            return False, 'Coupon has expired.'
        if self.max_uses and self.used_count >= self.max_uses:
            return False, 'Coupon usage limit reached.'
        if order_total < self.min_order_value:
            return False, f'Minimum order value is {self.min_order_value}.'
        return True, ''

    def calculate_discount(self, order_total: Decimal) -> Decimal:
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return (order_total * self.discount_value / 100).quantize(Decimal('0.01'))
        return min(self.discount_value, order_total)  # Fixed — مش هيطرح أكتر من الإجمالي


# ── Cart ──────────────────────────────────────────────────────────────
class Cart(models.Model):
    EXPIRY_DAYS = 7  # الكارت بتنتهي بعد 7 أيام من آخر تحديث

    user       = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    coupon     = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Cart of {self.user.email}'

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.updated_at + timedelta(days=self.EXPIRY_DAYS)

    @property
    def active_items(self):
        return self.items.filter(saved_for_later=False).select_related('variant__product')

    @property
    def saved_items(self):
        return self.items.filter(saved_for_later=True).select_related('variant__product')

    @property
    def subtotal(self) -> Decimal:
        return sum(item.total_price for item in self.active_items)

    @property
    def discount_amount(self) -> Decimal:
        if self.coupon:
            valid, _ = self.coupon.is_valid(self.subtotal)
            if valid:
                return self.coupon.calculate_discount(self.subtotal)
        return Decimal('0.00')

    @property
    def total(self) -> Decimal:
        return max(self.subtotal - self.discount_amount, Decimal('0.00'))

    @property
    def total_items(self) -> int:
        return sum(item.quantity for item in self.active_items)


# ── Cart Item ─────────────────────────────────────────────────────────
class CartItem(models.Model):
    MAX_QUANTITY = 10  # أقصى كمية لكل منتج

    cart           = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant        = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE)
    quantity       = models.PositiveSmallIntegerField(default=1)
    saved_for_later = models.BooleanField(default=False)  # Save for Later
    added_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'variant')  # نفس المنتج مرة واحدة بس في الكارت
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.quantity}x {self.variant} in {self.cart}'

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.quantity > self.MAX_QUANTITY:
            raise ValidationError(f'Maximum quantity per item is {self.MAX_QUANTITY}.')
        if self.quantity > self.variant.stock:
            raise ValidationError(f'Only {self.variant.stock} items in stock.')

    @property
    def unit_price(self) -> Decimal:
        return self.variant.effective_price

    @property
    def total_price(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal('0.01'))

    @property
    def is_available(self) -> bool:
        """هل المنتج لسه متاح بالكمية دي؟"""
        return self.variant.is_active and self.variant.product.is_active and self.variant.stock >= self.quantity
