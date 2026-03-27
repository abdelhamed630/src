from rest_framework import serializers
from .models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'full_name', 'email']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'sender', 'content', 'attachment', 'is_read', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    buyer        = UserMiniSerializer(read_only=True)
    seller       = UserMiniSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    order_number = serializers.CharField(source='order.order_number', read_only=True, default=None)

    class Meta:
        model  = Conversation
        fields = ['id', 'buyer', 'seller', 'order_number', 'last_message', 'unread_count', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.last_message
        if msg:
            return {'content': msg.content[:60], 'created_at': msg.created_at, 'sender_name': msg.sender.full_name}
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request:
            return obj.unread_count_for(request.user)
        return 0


class SendMessageSerializer(serializers.Serializer):
    content    = serializers.CharField(max_length=2000)
    attachment = serializers.FileField(required=False)
