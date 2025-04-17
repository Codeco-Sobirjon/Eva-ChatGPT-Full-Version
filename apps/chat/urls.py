from django.urls import path

from apps.chat.views import (
	ChatHistoryView, ChatHistoryDetailView, MessageDetailListView, ChatHistoryStatisticByWeekendView,
	ChatHistoryRemovedView, PaymentStatisticView, MessageStatisticView, UserStatisticView

)


urlpatterns = [
	path('', ChatHistoryView.as_view(), name='chat-history-list-create'),
	path('detail/<int:id>/', ChatHistoryDetailView.as_view(), name='chat-history-detail'),
	path('message/answer/<int:id>/', MessageDetailListView.as_view(), name='message-detail'),
	path('chat_history/statistics/', ChatHistoryStatisticByWeekendView.as_view(), name='chat-history-statistics'),
	path('chat_history/removed/', ChatHistoryRemovedView.as_view(), name='chat-history-removed'),
	path('payment/statistics/', PaymentStatisticView.as_view(), name='payment-statistics'),
	path('message/statistics/', MessageStatisticView.as_view(), name='message-statistics'),
	path('user/statistics/', UserStatisticView.as_view(), name='user-statistics'),

]
