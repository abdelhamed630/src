from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusLog
from accounts.models import Address


class AddressSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Address
        fields = ['full_name', 'phone', 'address_line1', 'address_line2',
                  'city', 'state', 'postal_code', 'country']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OrderItem
        fields = [
            'id', 'product_name', 'product_slug', 'variant_sku', 'variant_attrs',
            'product_image', 'quantity', 'unit_price', 'total_price',
            'item_status', 'tracking_number', 'shipped_at',
        ]


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True, default='System')

    class Meta:
        model  = OrderStatusLog
        fields = ['from_status', 'to_status', 'changed_by_name', 'note', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items       = OrderItemSerializer(many=True, read_only=True)
    status_logs = OrderStatusLogSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'order_number', 'status', 'payment_method', 'payment_status',
            'shipping_name', 'shipping_phone', 'shipping_address1', 'shipping_address2',
            'shipping_city', 'shipping_country',
            'subtotal', 'discount_amount', 'shipping_cost', 'total',
            'coupon_code', 'notes',
            'created_at', 'confirmed_at', 'shipped_at', 'delivered_at',
            'items', 'status_logs',
        ]


class PlaceOrderSerializer(serializers.Serializer):
    address_id     = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=Order.PaymentMethod.choices)
    notes          = serializers.CharField(required=False, allow_blank=True)


class UpdateOrderItemStatusSerializer(serializers.Serializer):
    """Seller updates item status + optional tracking"""
    item_status     = serializers.ChoiceField(choices=[
        ('processing','Processing'), ('shipped','Shipped'),
        ('delivered','Delivered'), ('cancelled','Cancelled')
    ])
    tracking_number = serializers.CharField(required=False, allow_blank=True)


class SellerOrderItemSerializer(serializers.ModelSerializer):
    """What a seller sees for their items in an order"""
    buyer_name  = serializers.CharField(source='order.buyer.full_name', read_only=True)
    buyer_email = serializers.CharField(source='order.buyer.email', read_only=True)
    buyer_phone = serializers.CharField(source='order.shipping_phone', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    order_date   = serializers.DateTimeField(source='order.created_at', read_only=True)
    shipping_address = serializers.CharField(source='order.full_shipping_address', read_only=True)

    class Meta:
        model  = OrderItem
        fields = [
            'id', 'order_number', 'order_date',
            'buyer_name', 'buyer_email', 'buyer_phone', 'shipping_address',
            'product_name', 'variant_sku', 'variant_attrs', 'product_image',
            'quantity', 'unit_price', 'total_price',
            'item_status', 'tracking_number', 'shipped_at',
        ]
