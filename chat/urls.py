from django.urls import path
from .views import ConversationListView, StartConversationView, ConversationDetailView, SendMessageView
app_name = 'chat'

urlpatterns = [
    path('',                    ConversationListView.as_view(),  name='conversation-list'),
    path('start/',              StartConversationView.as_view(), name='start-conversation'),
    path('<int:convo_id>/',     ConversationDetailView.as_view(), name='conversation-detail'),
    path('<int:convo_id>/send/', SendMessageView.as_view(),       name='send-message'),
]
