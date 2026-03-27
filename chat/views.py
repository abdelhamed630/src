from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer, SendMessageSerializer


class ConversationListView(APIView):
    """GET /chat/ — list all conversations for current user"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        convos = Conversation.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('buyer', 'seller', 'order').prefetch_related('messages')
        serializer = ConversationSerializer(convos, many=True, context={'request': request})
        return Response(serializer.data)


class StartConversationView(APIView):
    """
    POST /chat/start/
    { "seller_id": 5, "order_id": "uuid" (optional), "message": "Hi..." }
    Buyer starts a conversation with a seller.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        seller_id = request.data.get('seller_id')
        order_id  = request.data.get('order_id')
        content   = request.data.get('message', '').strip()

        if not seller_id:
            return Response({'detail': 'seller_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not content:
            return Response({'detail': 'Message content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        seller = get_object_or_404(User, id=seller_id, role='seller')

        if request.user == seller:
            return Response({'detail': 'Cannot message yourself.'}, status=status.HTTP_400_BAD_REQUEST)

        # Get or create conversation
        order = None
        if order_id:
            from orders.models import Order
            order = Order.objects.filter(id=order_id, buyer=request.user).first()

        convo, _ = Conversation.objects.get_or_create(
            buyer=request.user, seller=seller, order=order
        )

        msg = Message.objects.create(conversation=convo, sender=request.user, content=content)
        convo.save()  # Refresh updated_at

        return Response({
            'conversation_id': convo.id,
            'message': MessageSerializer(msg).data
        }, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """GET /chat/<id>/ — fetch messages in a conversation"""
    permission_classes = [IsAuthenticated]

    def get(self, request, convo_id):
        user  = request.user
        convo = get_object_or_404(
            Conversation.objects.filter(Q(buyer=user) | Q(seller=user)),
            id=convo_id
        )
        messages = convo.messages.select_related('sender')
        # Mark unread messages as read
        messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)


class SendMessageView(APIView):
    """POST /chat/<id>/send/ — send a message"""
    permission_classes = [IsAuthenticated]

    def post(self, request, convo_id):
        user  = request.user
        convo = get_object_or_404(
            Conversation.objects.filter(Q(buyer=user) | Q(seller=user)),
            id=convo_id
        )
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = Message.objects.create(
            conversation=convo,
            sender=user,
            content=serializer.validated_data['content'],
            attachment=serializer.validated_data.get('attachment'),
        )
        convo.save()

        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
