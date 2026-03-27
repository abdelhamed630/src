from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, VerifyOTPView, ResendOTPView,
    LoginView, GoogleAuthView, LogoutView, ProfileView,
    ChangePasswordView, ForgotPasswordView, ResetPasswordView,
    SellerRequestView, AddressListView, AddressDetailView,
    AdminUserListView, AdminUserDetailView,
    AdminSellerRequestListView, AdminSellerRequestDetailView,
)
app_name = 'accounts'

urlpatterns = [
    # Auth
    path('register/',         RegisterView.as_view(),       name='register'),
    path('verify-otp/',       VerifyOTPView.as_view(),       name='verify-otp'),
    path('resend-otp/',       ResendOTPView.as_view(),       name='resend-otp'),
    path('login/',            LoginView.as_view(),           name='login'),
    path('logout/',           LogoutView.as_view(),          name='logout'),
    path('google/',           GoogleAuthView.as_view(),      name='google-auth'),
    path('token/refresh/',    TokenRefreshView.as_view(),    name='token-refresh'),

    # Profile
    path('profile/',          ProfileView.as_view(),         name='profile'),

    # Password
    path('change-password/',  ChangePasswordView.as_view(),  name='change-password'),
    path('forgot-password/',  ForgotPasswordView.as_view(),  name='forgot-password'),
    path('reset-password/',   ResetPasswordView.as_view(),   name='reset-password'),

    # Seller
    path('seller-request/',   SellerRequestView.as_view(),   name='seller-request'),

    # Addresses
    path('addresses/',        AddressListView.as_view(),     name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),

    # Admin
    path('admin/users/',           AdminUserListView.as_view(),            name='admin-users'),
    path('admin/users/<int:pk>/',  AdminUserDetailView.as_view(),          name='admin-user-detail'),
    path('admin/seller-requests/', AdminSellerRequestListView.as_view(),   name='admin-seller-requests'),
    path('admin/seller-requests/<int:pk>/', AdminSellerRequestDetailView.as_view(), name='admin-seller-request-detail'),
]
