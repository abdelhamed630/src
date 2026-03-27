from django.urls import path
from .views import NotificationListView, NotificationMarkReadView, NotificationDetailView
app_name = 'notifications'

urlpatterns = [
    path('',             NotificationListView.as_view(),     name='list'),
    path('mark-read/',   NotificationMarkReadView.as_view(), name='mark-read'),
    path('<int:pk>/',    NotificationDetailView.as_view(),   name='detail'),
]
