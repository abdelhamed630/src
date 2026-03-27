from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusLog


class OrderItemInline(admin.TabularInline):
    model       = OrderItem
    extra       = 0
    readonly_fields = ['product_name', 'variant_sku', 'variant_attrs', 'quantity', 'unit_price', 'total_price', 'seller']
    fields      = ['product_name', 'variant_sku', 'quantity', 'unit_price', 'total_price', 'item_status', 'tracking_number', 'seller']
    can_delete  = False


class OrderStatusLogInline(admin.TabularInline):
    model      = OrderStatusLog
    extra      = 0
    readonly_fields = ['from_status', 'to_status', 'changed_by', 'note', 'created_at']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ['order_number', 'buyer_email', 'status', 'payment_method', 'total', 'created_at']
    list_filter     = ['status', 'payment_method', 'payment_status']
    search_fields   = ['order_number', 'buyer__email', 'shipping_name']
    readonly_fields = ['id', 'order_number', 'buyer', 'created_at', 'updated_at']
    ordering        = ['-created_at']
    inlines         = [OrderItemInline, OrderStatusLogInline]

    def buyer_email(self, obj):
        return obj.buyer.email
    buyer_email.short_description = 'Buyer'

    def save_model(self, request, obj, form, change):
        if change:
            old = Order.objects.get(pk=obj.pk)
            if old.status != obj.status:
                OrderStatusLog.objects.create(
                    order=obj, from_status=old.status,
                    to_status=obj.status, changed_by=request.user
                )
        super().save_model(request, obj, form, change)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ['order', 'product_name', 'seller', 'quantity', 'total_price', 'item_status']
    list_filter   = ['item_status']
    search_fields = ['product_name', 'order__order_number', 'seller__email']
    readonly_fields = ['order', 'seller', 'product', 'variant', 'product_name',
                       'variant_sku', 'variant_attrs', 'product_image', 'quantity',
                       'unit_price', 'total_price']
