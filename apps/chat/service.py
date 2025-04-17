import os

import openai
from functools import lru_cache
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from rest_framework import status

from apps.chat.models import ChatHistory, Message
from apps.prices_x_cards.models import Payment

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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
	def create_chat_history_and_message(user, message_content):

		check_pocket_buy_by_user = Payment.objects.select_related('user').filter(
			user=user
		).last()

		if not check_pocket_buy_by_user or check_pocket_buy_by_user.status != 'success':
			raise ValueError('Пользователь пока не приобрёл ни одного тарифа.', status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			chat_history_exists = ChatHistory.objects.select_related('user').filter(user=user, is_active=True).last()

			if chat_history_exists:

				chat_message_exists = Message.objects.select_related('chat_history').filter(
					chat_history=chat_history_exists, first_message=True
				).last()

				if chat_message_exists:

					if int(chat_message_exists.chat_history.request_count) < int(check_pocket_buy_by_user.product_pocket.count_typing):

						Message.objects.create(
							chat_history=chat_history_exists,
							question=message_content,
							first_message=False
						)
						chat_history_exists.request_count += 1
						chat_history_exists.save()
						return chat_history_exists

					else:

						chat_history_exists.is_active=False
						chat_history_exists.save()
						raise ObjectDoesNotExist(
							f'Лимит чатов для данного тарифа {check_pocket_buy_by_user.product_pocket.title} исчерпан.'
						)

				Message.objects.create(
					chat_history=chat_history_exists, question=message_content, first_message=True
				)

				chat_history_exists.request_count += 1
				chat_history_exists.save()

				return chat_history_exists

			raise ObjectDoesNotExist('Пользователь пока не приобрёл ни одного тарифа.')
