from django.urls import path
from .views import ProductReviewListView, ReviewDetailView, SellerReplyView, MarkReviewHelpfulView
app_name = 'reviews'

urlpatterns = [
    path('products/<slug:slug>/',  ProductReviewListView.as_view(), name='product-reviews'),
    path('<int:pk>/',              ReviewDetailView.as_view(),       name='review-detail'),
    path('<int:pk>/reply/',        SellerReplyView.as_view(),        name='review-reply'),
    path('<int:pk>/helpful/',      MarkReviewHelpfulView.as_view(),  name='review-helpful'),
]
