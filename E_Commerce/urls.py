from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',             admin.site.urls),
    path('api/accounts/',      include('accounts.urls',      namespace='accounts')),
    path('api/products/',      include('products.urls',      namespace='products')),
    path('api/cart/',          include('cart.urls',          namespace='cart')),
    path('api/orders/',        include('orders.urls',        namespace='orders')),
    path('api/chat/',          include('chat.urls',          namespace='chat')),
    path('api/reviews/',       include('reviews.urls',       namespace='reviews')),
    path('api/wishlist/',      include('wishlist.urls',      namespace='wishlist')),
    path('api/notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
