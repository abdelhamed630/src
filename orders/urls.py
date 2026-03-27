from django.urls import path
from .views import (
    SellerDashboardView,
    PlaceOrderView, BuyerOrderListView, BuyerOrderDetailView,
    DownloadInvoiceView, SellerOrderListView,
    SellerUpdateOrderItemView, SellerDownloadInvoiceView,
    AdminOrderListView,
)
app_name = 'orders'

urlpatterns = [
    # Buyer
    path('place/',                              PlaceOrderView.as_view(),           name='place-order'),
    path('',                                    BuyerOrderListView.as_view(),        name='order-list'),
    path('<str:order_number>/',                 BuyerOrderDetailView.as_view(),      name='order-detail'),
    path('<str:order_number>/invoice/',         DownloadInvoiceView.as_view(),       name='download-invoice'),

    # Seller
    path('seller/dashboard/',                   SellerDashboardView.as_view(),       name='seller-dashboard'),
    path('seller/orders/',                      SellerOrderListView.as_view(),       name='seller-orders'),
    path('seller/items/<int:item_id>/update/',  SellerUpdateOrderItemView.as_view(), name='seller-update-item'),
    path('seller/items/<int:item_id>/invoice/', SellerDownloadInvoiceView.as_view(), name='seller-invoice'),

    # Admin
    path('admin/',                              AdminOrderListView.as_view(),        name='admin-orders'),
]
