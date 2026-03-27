from django.contrib import admin
from .models import Review

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['product', 'buyer', 'rating', 'is_verified_purchase', 'helpful_count', 'created_at']
    list_filter   = ['rating', 'is_verified_purchase']
    search_fields = ['product__name', 'buyer__email', 'body']
    readonly_fields = ['buyer', 'product', 'order_item', 'is_verified_purchase', 'helpful_count', 'created_at']
