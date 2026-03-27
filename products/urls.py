from django.urls import path
from .views import (
    SearchSuggestionsView,
    CategoryListView,
    ProductListView,
    ProductDetailView,
    FeaturedProductsView,
    BestSellerProductsView,
    OnSaleProductsView,
    SellerProductListView,
    SellerProductDetailView,
)
app_name = 'products'

urlpatterns = [
    # Public
    path('categories/',            CategoryListView.as_view(),       name='category-list'),
    path('',                       ProductListView.as_view(),         name='product-list'),
    path('featured/',              FeaturedProductsView.as_view(),    name='product-featured'),
    path('best-sellers/',          BestSellerProductsView.as_view(),  name='product-best-sellers'),
    path('on-sale/',               OnSaleProductsView.as_view(),      name='product-on-sale'),

    # Seller management
    path('my-products/',           SellerProductListView.as_view(),   name='seller-product-list'),
    path('my-products/<slug:slug>/', SellerProductDetailView.as_view(), name='seller-product-detail'),

    # Search
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search-suggestions'),

    # Public product detail (must be last)
    path('<slug:slug>/',            ProductDetailView.as_view(),       name='product-detail'),
]
