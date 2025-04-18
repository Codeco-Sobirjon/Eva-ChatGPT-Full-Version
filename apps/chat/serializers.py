from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.chat.models import Message, ChatHistory, Answer
from apps.accounts.serializers import CustomUserDetailSerializer
from apps.prices_x_cards.models import Payment

from apps.chat.service import chatbot_response, ChatService


class ChatHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatHistory
        fields = ["id", "user", "created", "is_active"]

    def create(self, validated_data):
        user = self.context.get('request').user

        chat_history_user_is_active_change = ChatHistory.objects.filter(user=user).update(is_active=False)
        chat_history = ChatHistory.objects.create(**validated_data, user=user, is_active=True)
        return chat_history


class MessageListUserSerializer(serializers.ModelSerializer):
    chat_history = ChatHistoryCreateSerializer(read_only=True)
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "question", "created", "chat_history"]

    def get_answer(self, obj):
        get_answer = Answer.objects.select_related('message').filter(message=obj).first()
        serializer = AnswerSerializer(get_answer, context={'request': self.context.get('request')})
        return serializer.data


class ChatHistorySerializer(serializers.ModelSerializer):
    message = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = ChatHistory
        fields = ["id", "user", "created", "is_active", "message"]
        read_only_fields = ["id", "user", "created", "is_active"]

    def validate_message(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty.")
        return value

    def update(self, instance, validated_data):
        user = self.context.get('request').user
        message_content = validated_data.pop('message', None)
        chat_history_id = self.context.get('chat_history_id')

        try:
            chat_history = ChatService.create_chat_history_and_message(
                user, message_content, chat_history_id
            )
            return chat_history
        except ValidationError as e:
            if isinstance(e.detail, (list, tuple)) and len(e.detail) > 0:
                error_message = str(e.detail[0])
            elif isinstance(e.detail, dict):
                key, val = list(e.detail.items())[0]
                error_message = str(val[0]) if isinstance(val, list) else str(val)
            else:
                error_message = str(e.detail)

            raise serializers.ValidationError({"message": error_message})



class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["id", "answer", "created"]


class MessageSerializer(serializers.ModelSerializer):
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "question",  "answer", "created"]

    def get_answer(self, obj):
        get_answer = Answer.objects.select_related('message').filter(message=obj).first()
        serializer = AnswerSerializer(get_answer, context={'request': self.context.get('request')})
        return serializer.data


class ChatHistoryDetailSerializer(serializers.ModelSerializer):
    user = CustomUserDetailSerializer(read_only=True)
    message_list = serializers.SerializerMethodField()
    first_msg = serializers.SerializerMethodField()

    class Meta:
        model = ChatHistory
        fields = ["id", "user", "created", "is_active", "message_list", "first_msg"]

    def get_message_list(self, obj):
        messages = Message.objects.filter(chat_history=obj)
        serializer = MessageSerializer(messages, many=True, context={'request': self.context.get('request')})
        return serializer.data

    def get_first_msg(self, obj):
        first_msg = Message.objects.filter(chat_history=obj, first_message=True).first()
        serializer = MessageSerializer(first_msg, context={'request': self.context.get('request')})
        return serializer.data
