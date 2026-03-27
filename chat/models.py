"""
Real-time chat between buyer and seller (like Amazon messaging).
One conversation per (buyer, seller) pair.
"""
from django.db import models
from django.conf import settings


class Conversation(models.Model):
    buyer      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_conversations')
    seller     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_conversations')
    order      = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('buyer', 'seller', 'order')
        ordering = ['-updated_at']

    def __str__(self):
        return f'Chat: {self.buyer.email} ↔ {self.seller.email}'

    @property
    def last_message(self):
        return self.messages.order_by('-created_at').first()

    def unread_count_for(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content      = models.TextField()
    attachment   = models.FileField(upload_to='chat/attachments/', blank=True, null=True)
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.created_at:%H:%M}] {self.sender.full_name}: {self.content[:40]}'
