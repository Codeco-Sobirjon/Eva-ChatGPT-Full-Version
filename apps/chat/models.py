from django.db import models
from apps.accounts.models import CustomUser
from apps.prices_x_cards.models import ProductPocket


class ChatHistory(models.Model):
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="chat_histories", verbose_name="Пользователь",
	                         null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True, blank=True)
	is_active = models.BooleanField(default=True, verbose_name="Активный статус", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"{self.user.username}: {self.id}"

	class Meta:
		verbose_name = "История чата"
		verbose_name_plural = "Истории чатов"
		ordering = ["-created"]


class Message(models.Model):
	chat_history = models.ForeignKey(ChatHistory, on_delete=models.CASCADE, related_name="messages",
	                                 verbose_name="История чата", null=True, blank=True)
	question = models.TextField(verbose_name="Вопрос", null=True, blank=True)
	first_message = models.BooleanField(default=True, verbose_name="Первое сообщение", null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"Сообщение {self.chat_history}"

	class Meta:
		verbose_name = "Сообщение"
		verbose_name_plural = "Сообщения"
		ordering = ["-created"]


class Answer(models.Model):
	message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="answers", verbose_name="Сообщение")
	answer = models.TextField(verbose_name="Ответ", null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"Ответ {self.id} - {self.message.id}"

	class Meta:
		verbose_name = "Ответ"
		verbose_name_plural = "Ответы"
		ordering = ["created"]


class RequestCount(models.Model):
	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="request_counts", verbose_name="Пользователь")
	request_count = models.PositiveIntegerField(default=0, verbose_name="Количество запросов", null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания", null=True, blank=True)
	is_active = models.BooleanField(default=True, verbose_name="Активный статус", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"{self.user.username}"

	class Meta:
		verbose_name = "Количество запросов"
		verbose_name_plural = "Количество запросов"
		ordering = ["-created"]

