from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model      = Message
    extra      = 0
    readonly_fields = ['sender', 'content', 'is_read', 'created_at']
    can_delete = False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display  = ['id', 'buyer', 'seller', 'order', 'updated_at']
    search_fields = ['buyer__email', 'seller__email']
    inlines       = [MessageInline]
