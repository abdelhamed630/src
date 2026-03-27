from django.urls import path
from .views import (
    CartView, AddToCartView,
    UpdateCartItemView, RemoveCartItemView,
    SaveForLaterView, ApplyCouponView, CartSummaryView,
)
app_name = 'cart'
urlpatterns = [
    # الكارت الرئيسية
    path('',              CartView.as_view(),         name='cart'),           # GET / DELETE
    path('summary/',      CartSummaryView.as_view(),  name='cart-summary'),   # GET خفيف

    # إضافة منتج
    path('add/',          AddToCartView.as_view(),    name='cart-add'),       # POST

    # عمليات على الأيتمز
    path('items/<int:item_id>/',              UpdateCartItemView.as_view(), name='cart-item-update'),  # PATCH
    path('items/<int:item_id>/remove/',       RemoveCartItemView.as_view(), name='cart-item-remove'),  # DELETE
    path('items/<int:item_id>/save/',         SaveForLaterView.as_view(),   name='cart-item-save',   kwargs={'action': 'save'}),  # POST
    path('items/<int:item_id>/move-to-cart/', SaveForLaterView.as_view(),   name='cart-item-move',   kwargs={'action': 'move'}),  # POST

    # كوبون
    path('coupon/',       ApplyCouponView.as_view(),  name='cart-coupon'),    # POST / DELETE
]
