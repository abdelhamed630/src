from django.contrib import admin
from .models import Category, Tag, Product, ProductImage, Attribute, AttributeValue, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ['name', 'parent', 'level', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ['sku', 'attribute_values', 'price_override', 'stock', 'is_active']
    filter_horizontal = ['attribute_values']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'product_type', 'base_price', 'discount_price', 'is_active', 'is_featured', 'is_best_seller']
    list_filter   = ['is_active', 'is_featured', 'is_best_seller', 'product_type', 'category']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal   = ['tags', 'related_products']
    inlines = [ProductImageInline, ProductVariantInline]
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Info',   {'fields': ('name', 'slug', 'description', 'category', 'tags', 'product_type')}),
        ('Pricing',      {'fields': ('base_price', 'discount_price')}),
        ('Digital',      {'fields': ('digital_file',), 'classes': ('collapse',)}),
        ('Flags',        {'fields': ('is_active', 'is_featured', 'is_best_seller')}),
        ('Relations',    {'fields': ('related_products',)}),
        ('Timestamps',   {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display  = ['attribute', 'value']
    list_filter   = ['attribute']
    search_fields = ['value']
