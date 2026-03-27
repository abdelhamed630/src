from django.urls import path
from .views import WishlistView, WishlistToggleView, WishlistCheckView
app_name = 'wishlist'

urlpatterns = [
    path('',                    WishlistView.as_view(),       name='wishlist'),
    path('<slug:slug>/',        WishlistToggleView.as_view(), name='wishlist-toggle'),
    path('check/<slug:slug>/',  WishlistCheckView.as_view(),  name='wishlist-check'),
]
