from pathlib import Path
import os

import openai
from functools import lru_cache
from django.db import transaction
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status

from apps.chat.models import ChatHistory, Message, RequestCount
from apps.prices_x_cards.models import Payment
from dotenv import load_dotenv
from apps.chat.load_env import load_env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



client = openai.OpenAI(
	api_key=OPENAI_API_KEY)


@lru_cache(maxsize=100)
def cached_response(user_message, language):
	return chatbot_response_core(user_message, language)


def detect_language(text):
	text_lower = text.lower()

	if "o‘" in text_lower or "g‘" in text_lower or "salom" in text_lower or "kasallik" in text_lower:
		return "uz"

	if any(ord('а') <= ord(c) <= ord('я') or c == 'ё' for c in text_lower):
		return "ru"

	if any(c.isalpha() and c in "abcdefghijklmnopqrstuvwxyz" for c in text_lower):
		return "en"

	return None


def chatbot_response_core(user_message, language):
    try:
        prompt = (
            f"First, determine if the following question is related to health, diseases, or medicines. "
            f"If it is not, respond with: "
            f"'I can only answer questions related to health, diseases, and medicines.' (in English), "
            f"'Я могу отвечать только на вопросы, связанные со здоровьем, болезнями и лекарствами.' (in Russian), "
            f"or 'Men faqat sog‘liq, kasallik va dori-darmon haqidagi savollarga javob bera olaman.' (in Uzbek), "
            f"depending on the language '{language}'. "
            f"If it is related, provide an accurate and helpful answer in the same language as the input. "
            f"Question: {user_message}"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a medical assistant that only answers questions related to health, diseases, and medicines. "
                        "You respond in Russian, English, or Uzbek, based on the user's input language. "
                        "If the question is not related to health, return the specified rejection message in the correct language."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        import traceback
        print("=" * 50)
        print("❌ Xatolik yuz berdi:")
        print("Xatolik turi:", type(e).__name__)
        print("Xatolik matni:", str(e))
        print("Traceback:")
        traceback.print_exc()
        print("=" * 50)

        if language == "ru":
            return "Извините, произошла ошибка. Пожалуйста, попробуйте снова."
        elif language == "uz":
            return "Kechirasiz, xato yuz berdi. Iltimos, qayta urinib ko‘ring."
        else:
            return "Sorry, an error occurred. Please try again."


def chatbot_response(user_message):
	language = detect_language(user_message)

	if language not in ["ru", "en", "uz"]:
		if language == "ru":
			return "Пожалуйста, пишите только на русском, английском или узбекском языке."
		elif language == "uz":
			return "Iltimos, faqat rus, ingliz yoki o‘zbek tilida yozing."
		else:
			return "Please write only in Russian, English, or Uzbek."

	return cached_response(user_message, language)


class ChatService:
    @staticmethod
    def create_chat_history_and_message(user, message_content, chat_history_id):
        chat_history = ChatHistory.objects.filter(pk=chat_history_id).first()
        if not chat_history:
            raise ValidationError("История чата не найдена.")

        request_count = RequestCount.objects.filter(user=user).order_by('-id').first()
        if not request_count:
            request_count = RequestCount.objects.create(user=user, request_count=0)

        payment = Payment.objects.filter(user=user, status='success').last()

        if not payment and request_count.request_count > 0:
            raise ValidationError("Вы уже использовали бесплатный запрос. Для продолжения приобретите тариф.")

        allowed_typing_count = 1 if not payment else payment.product_pocket.count_typing

        with transaction.atomic():
            first_message = Message.objects.filter(
                chat_history=chat_history, first_message=True
            ).last()

            if request_count.request_count < allowed_typing_count:
                message = Message.objects.create(
                    chat_history=chat_history,
                    question=message_content,
                    first_message=not bool(first_message)
                )
            else:
                chat_history.is_active = False
                chat_history.save()
                raise ValidationError('Лимит чатов для тарифа исчерпан.')

            request_count.request_count += 1
            request_count.save()

            return message
