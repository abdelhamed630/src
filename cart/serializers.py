from rest_framework import serializers
from .models import Cart, CartItem, Coupon


# ── Cart Item ─────────────────────────────────────────────────────────
class CartItemSerializer(serializers.ModelSerializer):
    product_name   = serializers.CharField(source='variant.product.name',        read_only=True)
    product_slug   = serializers.CharField(source='variant.product.slug',        read_only=True)
    variant_attrs  = serializers.SerializerMethodField()
    unit_price     = serializers.DecimalField(max_digits=10, decimal_places=2,   read_only=True)
    total_price    = serializers.DecimalField(max_digits=10, decimal_places=2,   read_only=True)
    stock          = serializers.IntegerField(source='variant.stock',            read_only=True)
    is_available   = serializers.BooleanField(read_only=True)
    primary_image  = serializers.SerializerMethodField()

    class Meta:
        model  = CartItem
        fields = [
            'id', 'variant', 'product_name', 'product_slug',
            'variant_attrs', 'quantity', 'unit_price', 'total_price',
            'stock', 'is_available', 'saved_for_later',
            'primary_image', 'added_at',
        ]
        read_only_fields = ['added_at']

    def get_variant_attrs(self, obj):
        return [
            {'attribute': av.attribute.name, 'value': av.value}
            for av in obj.variant.attribute_values.select_related('attribute').all()
        ]

    def get_primary_image(self, obj):
        image = obj.variant.product.images.filter(is_primary=True).first() \
             or obj.variant.product.images.first()
        if image and image.thumbnail:
            request = self.context.get('request')
            return request.build_absolute_uri(image.thumbnail.url) if request else image.thumbnail.url
        return None


# ── Add to Cart ───────────────────────────────────────────────────────
class AddToCartSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity   = serializers.IntegerField(min_value=1, max_value=CartItem.MAX_QUANTITY)

    def validate(self, attrs):
        from products.models import ProductVariant
        try:
            variant = ProductVariant.objects.select_related('product').get(pk=attrs['variant_id'])
        except ProductVariant.DoesNotExist:
            raise serializers.ValidationError({'variant_id': 'Variant not found.'})

        if not variant.is_active or not variant.product.is_active:
            raise serializers.ValidationError({'variant_id': 'Product is not available.'})

        if variant.stock < attrs['quantity']:
            raise serializers.ValidationError({'quantity': f'Only {variant.stock} items in stock.'})

        attrs['variant'] = variant
        return attrs


# ── Update Quantity ───────────────────────────────────────────────────
class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=CartItem.MAX_QUANTITY)

    def validate_quantity(self, value):
        # التحقق من الـ stock هيتم في الـ view
        return value


# ── Apply Coupon ──────────────────────────────────────────────────────
class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=50)


# ── Cart Summary ──────────────────────────────────────────────────────
class CartSerializer(serializers.ModelSerializer):
    items           = serializers.SerializerMethodField()
    saved_items     = serializers.SerializerMethodField()
    subtotal        = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total           = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_items     = serializers.IntegerField(read_only=True)
    coupon_code     = serializers.CharField(source='coupon.code', read_only=True, allow_null=True)
    is_expired      = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Cart
        fields = [
            'id', 'total_items', 'subtotal', 'discount_amount', 'total',
            'coupon_code', 'is_expired', 'items', 'saved_items', 'updated_at',
        ]

    def get_items(self, obj):
        return CartItemSerializer(obj.active_items, many=True, context=self.context).data

    def get_saved_items(self, obj):
        return CartItemSerializer(obj.saved_items, many=True, context=self.context).data
