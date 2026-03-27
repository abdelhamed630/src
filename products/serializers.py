from rest_framework import serializers
from .models import Category, Tag, Product, ProductImage, Attribute, AttributeValue, ProductVariant


# ── Category ──────────────────────────────────────────────────────────
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'image', 'parent', 'children', 'level', 'is_active']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True, context=self.context).data


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug']


# ── Tag ───────────────────────────────────────────────────────────────
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Tag
        fields = ['id', 'name', 'slug']


# ── Product Image ─────────────────────────────────────────────────────
class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']


# ── Attribute & Values ────────────────────────────────────────────────
class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model  = AttributeValue
        fields = ['id', 'attribute_name', 'value']


# ── Product Variant ───────────────────────────────────────────────────
class ProductVariantSerializer(serializers.ModelSerializer):
    attribute_values = AttributeValueSerializer(many=True, read_only=True)
    effective_price  = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock         = serializers.BooleanField(read_only=True)

    class Meta:
        model  = ProductVariant
        fields = [
            'id', 'sku', 'attribute_values',
            'price_override', 'effective_price',
            'stock', 'in_stock', 'is_active',
        ]


# ── Product List (خفيف للقوائم) ───────────────────────────────────────
class ProductListSerializer(serializers.ModelSerializer):
    primary_image       = serializers.SerializerMethodField()
    category            = CategoryMiniSerializer(read_only=True)
    effective_price     = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_on_sale          = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'category',
            'base_price', 'discount_price', 'effective_price',
            'discount_percentage', 'is_on_sale',
            'is_featured', 'is_best_seller', 'product_type',
            'primary_image',
        ]

    def get_primary_image(self, obj):
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            return ProductImageSerializer(image, context=self.context).data
        return None


# ── Product Detail (تفاصيل كاملة) ────────────────────────────────────
class ProductDetailSerializer(serializers.ModelSerializer):
    category            = CategoryMiniSerializer(read_only=True)
    tags                = TagSerializer(many=True, read_only=True)
    images              = ProductImageSerializer(many=True, read_only=True)
    variants            = ProductVariantSerializer(many=True, read_only=True)
    related_products    = ProductListSerializer(many=True, read_only=True)
    effective_price     = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    is_on_sale          = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Product
        fields = [
            'id', 'name', 'slug', 'description', 'product_type',
            'category', 'tags',
            'base_price', 'discount_price', 'effective_price',
            'discount_percentage', 'is_on_sale',
            'is_featured', 'is_best_seller', 'is_active',
            'images', 'variants', 'related_products',
            'digital_file',
            'created_at', 'updated_at',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.product_type != 'digital':
            data.pop('digital_file', None)
        return data


# ── Product Create/Update (Seller) ────────────────────────────────────
class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = [
            'name', 'description', 'product_type',
            'category', 'base_price', 'discount_price',
            'is_active', 'is_featured',
        ]

    def validate(self, attrs):
        if attrs.get('discount_price') and attrs.get('base_price'):
            if attrs['discount_price'] >= attrs['base_price']:
                raise serializers.ValidationError({'discount_price': 'Discount price must be less than base price.'})
        return attrs
