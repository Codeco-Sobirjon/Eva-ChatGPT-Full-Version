from django.contrib import admin

from apps.chat.models import Message, ChatHistory, Answer, RequestCount


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('chat_history', 'question', 'created', 'first_message')


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
	list_display = ('user', 'created')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
	list_display = ('message', 'answer', 'created')


@admin.register(RequestCount)
class RequestCountAdmin(admin.ModelAdmin):
    list_display = ['id', 'request_count', 'user']
