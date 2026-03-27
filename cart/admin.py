from django.contrib import admin
from .models import Cart, CartItem, Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ['code', 'discount_type', 'discount_value', 'min_order_value', 'used_count', 'max_uses', 'is_active', 'expires_at']
    list_filter   = ['discount_type', 'is_active']
    search_fields = ['code']
    readonly_fields = ['used_count']


class CartItemInline(admin.TabularInline):
    model  = CartItem
    extra  = 0
    fields = ['variant', 'quantity', 'saved_for_later', 'added_at']
    readonly_fields = ['added_at']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display  = ['user', 'total_items', 'total', 'coupon', 'is_expired', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]

    def total_items(self, obj):
        return obj.total_items

    def total(self, obj):
        return obj.total

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
