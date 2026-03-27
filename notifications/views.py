from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    """GET /notifications/ — list all notifications for current user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user)
        unread_count = notifs.filter(is_read=False).count()
        return Response({
            'unread_count': unread_count,
            'notifications': NotificationSerializer(notifs[:50], many=True).data,
        })


class NotificationMarkReadView(APIView):
    """POST /notifications/mark-read/ — mark all as read"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'detail': 'All notifications marked as read.'})


class NotificationDetailView(APIView):
    """DELETE /notifications/<id>/ — delete single notification"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        notif = get_object_or_404(Notification, id=pk, user=request.user)
        notif.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pk):
        """Mark single notification as read"""
        notif = get_object_or_404(Notification, id=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return Response(NotificationSerializer(notif).data)
