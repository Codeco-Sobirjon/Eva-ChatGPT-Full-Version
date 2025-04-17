from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.chat.models import Message, ChatHistory, Answer
from apps.accounts.serializers import CustomUserDetailSerializer
from apps.prices_x_cards.models import Payment

from apps.chat.service import chatbot_response, ChatService


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

    def create(self, validated_data):
        user = self.context.get('request').user
        message_content = validated_data.pop('message', None)

        try:
            chat_history = ChatService.create_chat_history_and_message(user, message_content)
            return chat_history
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        return representation


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
