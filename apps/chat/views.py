import difflib
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Sum
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.accounts.models import CustomUser
from apps.accounts.serializers import CustomUserDetailSerializer
from apps.chat.models import Message, ChatHistory, Answer
from apps.chat.serializers import ChatHistorySerializer, ChatHistoryDetailSerializer, ChatHistoryCreateSerializer, \
    MessageListUserSerializer
from apps.chat.service import chatbot_response
from apps.prices_x_cards.models import Payment


class ChatHistoryCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChatHistoryCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            chat_history = serializer.save()
            return Response({"message": "Chat history created successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageListUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        chat_history = get_object_or_404(ChatHistory, id=kwargs['id'])
        messages = Message.objects.filter(chat_history=chat_history)
        serializer = MessageListUserSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)


class TypingView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Send typing status to the chatbot.",
        tags=['Chat History'],
        responses={
            200: openapi.Response(
                description="Typing status sent successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Typing status sent successfully.")
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        chat_history = ChatHistory.objects.filter(id=kwargs['id']).first()
        if not chat_history:
            return Response({"message": "Пользователь пока не приобрёл ни одного тарифа."}, status=status.HTTP_202_ACCEPTED)

        serializer = ChatHistorySerializer(
            chat_history,
            data=request.data,
            context={'request': request, 'chat_history_id': chat_history.id}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatHistoryRemovedView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete all chat histories and associated messages for the authenticated user.",
        tags=['Chat History'],
        responses={
            204: openapi.Response(
                description="Chat history deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Chat history deleted successfully.")
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        chat_history = ChatHistory.objects.select_related('user').filter(user=request.user)
        chat_history.delete()
        messages = Message.objects.select_related('chat_history').filter(chat_history__user=request.user)
        messages.delete()
        return Response({"message": "Chat history deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class ChatHistoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific chat history by ID.",
        tags=['Chat History'],
        responses={
            200: ChatHistoryDetailSerializer(many=False),
            404: openapi.Response(
                description="Chat history not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        chat_history_id = kwargs['id']
        chat_history = get_object_or_404(ChatHistory, id=chat_history_id)
        serializer = ChatHistoryDetailSerializer(chat_history, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Delete a specific chat history and its associated messages by ID.",
        tags=['Chat History'],
        responses={
            204: openapi.Response(
                description="Chat history deleted successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example="Chat history deleted successfully.")
                    }
                )
            ),
            404: openapi.Response(
                description="Chat history not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def delete(self, request, *args, **kwargs):
        chat_history_id = kwargs['id']
        chat_history = get_object_or_404(ChatHistory, id=chat_history_id)
        messages = Message.objects.select_related('chat_history').filter(chat_history=chat_history)
        messages.delete()
        chat_history.delete()
        return Response({"message": "Chat history deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class MessageDetailListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate and store an answer for a specific message by ID using a chatbot.",
        tags=['Messages'],
        responses={
            201: openapi.Response(
                description="Answer successfully added.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'msg': openapi.Schema(type=openapi.TYPE_STRING, example="Successfull added")
                    }
                )
            ),
            404: openapi.Response(
                description="Message not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        message_id = kwargs['id']
        msg_data = get_object_or_404(Message, id=message_id)
        get_answer = chatbot_response(msg_data.question)
        create_answer_to_msg = Answer.objects.create(
            message=msg_data,
            answer=get_answer
        )
        return Response({'msg': "Successfull added"}, status=status.HTTP_201_CREATED)


class ChatHistoryStatisticByWeekendView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve chat history statistics for the past 7 days for the authenticated user.",
        tags=['Chat History Statistics'],
        responses={
            200: openapi.Response(
                description="Chat history statistics for the past 7 days.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'today': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            'yesterday': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            '2_days_ago': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            '3_days_ago': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            '4_days_ago': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            '5_days_ago': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                            '6_days_ago': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    description="Chat history details"
                                )
                            ),
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        today = now().date()
        chat_history = ChatHistory.objects.filter(user=request.user)

        result = []

        for i in range(7):
            day_date = today - timedelta(days=i)
            day_chats = chat_history.filter(created__date=day_date)
            serialized = ChatHistoryDetailSerializer(day_chats, many=True).data

            if i == 0:
                key = "today"
            elif i == 1:
                key = "yesterday"
            else:
                key = f"{i}_days_ago"

            result.append({
                key: serialized
            })

        return Response(result)


class UserStatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve statistics for all users, including their details and message counts.",
        tags=['User Statistics'],
        responses={
            200: openapi.Response(
                description="User statistics.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'user_info': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description="User details"
                            ),
                            'messages_count': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Number of messages"
                            )
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        users = CustomUser.objects.all()
        response_data = []

        for user in users:
            user_messages_count = Message.objects.select_related('chat_history').filter(chat_history__user=user).count()
            user_info = CustomUserDetailSerializer(user, context={'request': request}).data

            response_data.append({
                "user_info": user_info,
                "messages_count": user_messages_count
            })

        return Response(response_data, status=status.HTTP_200_OK)


class MessageStatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Group messages by similarity based on their content and provide counts.",
        tags=['Message Statistics'],
        responses={
            200: openapi.Response(
                description="Grouped message statistics.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'messages_info': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description="Similar message content"
                                )
                            ),
                            'messages_count': openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                description="Number of similar messages"
                            )
                        }
                    )
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        messages = Message.objects.all().values_list('question', flat=True)
        messages = list(messages)

        grouped = []
        used = set()

        for i, msg in enumerate(messages):
            if msg in used:
                continue

            group = [msg]
            used.add(msg)

            similar = difflib.get_close_matches(msg, messages, n=10, cutoff=0.7)

            for sim in similar:
                if sim != msg and sim not in used:
                    group.append(sim)
                    used.add(sim)

            grouped.append({
                "messages_info": group,
                "messages_count": len(group)
            })

        return Response(grouped, status=status.HTTP_200_OK)


class PaymentStatisticView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve payment statistics aggregated by month or day for a specified range (7, 30, 6 months, or 12 months).",
        tags=['Payment Statistics'],
        manual_parameters=[
            openapi.Parameter(
                name='range',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=['7', '30', '6', '12'],
                default='12',
                description="Time range for statistics: 7 (days), 30 (days), 6 (months), 12 (months)"
            )
        ],
        responses={
            200: openapi.Response(
                description="Payment statistics.",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'date': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                format='date',
                                description="Date of the period"
                            ),
                            'amount': openapi.Schema(
                                type=openapi.TYPE_NUMBER,
                                description="Total payment amount"
                            )
                        }
                    )
                )
            ),
            400: openapi.Response(
                description="Invalid range parameter.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Invalid range"
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        range_type = request.query_params.get("range", "12")

        now = timezone.now()

        if range_type == "12":
            start_date = now - timedelta(days=365)
            payments = (
                Payment.objects.filter(created__gte=start_date)
                .annotate(period=TruncMonth("created"))
                .values("period")
                .annotate(total=Sum("amount"))
                .order_by("period")
            )

        elif range_type == "6":
            start_date = now - timedelta(days=180)
            payments = (
                Payment.objects.filter(created__gte=start_date)
                .annotate(period=TruncMonth("created"))
                .values("period")
                .annotate(total=Sum("amount"))
                .order_by("period")
            )

        elif range_type == "30":
            start_date = now - timedelta(days=30)
            payments = (
                Payment.objects.filter(created__gte=start_date)
                .annotate(period=TruncDay("created"))
                .values("period")
                .annotate(total=Sum("amount"))
                .order_by("period")
            )

        elif range_type == "7":
            start_date = now - timedelta(days=7)
            payments = (
                Payment.objects.filter(created__gte=start_date)
                .annotate(period=TruncDay("created"))
                .values("period")
                .annotate(total=Sum("amount"))
                .order_by("period")
            )

        else:
            return Response({"error": "Invalid range"}, status=400)

        data = [
            {
                "date": p["period"].strftime("%Y-%m-%d"),
                "amount": p["total"] or 0
            }
            for p in payments
        ]

        return Response(data)
