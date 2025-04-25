from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ProductPocket(models.Model):
	PRICE_TYPE_CHOICES = [('RUB', 'Рубли'), ('USD', 'Доллары')]

	title = models.CharField(max_length=255, verbose_name="Название", null=True, blank=True)
	description = models.TextField(verbose_name="Описание", null=True, blank=True)
	price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена", null=True, blank=True)
	price_type = models.CharField(max_length=3, choices=PRICE_TYPE_CHOICES, verbose_name="Тип валюты", null=True,
	                              blank=True)
	count_typing = models.PositiveIntegerField(default=1, verbose_name="Количество вводов", null=True, blank=True)

	objects = models.Manager()
	@property
	def price_digits(self): return len(
		str(self.price).replace('.', '').replace(',', '')) if self.price is not None else 0

	def __str__(self): return f"{self.title} - {self.price} {self.get_price_type_display()}"

	class Meta:
		verbose_name = "Тариф"
		verbose_name_plural = "Тарифы"


class Card(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
	card_number = models.CharField(max_length=19, verbose_name="Номер карты", null=True, blank=True)
	expiry_date = models.CharField(max_length=5, verbose_name="Срок действия (MM/YY)", null=True, blank=True)
	cardholder_name = models.CharField(max_length=100, verbose_name="Имя владельца", null=True, blank=True)
	added = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"Карта {self.card_number[-4:]} пользователя {self.user}"

	class Meta:
		verbose_name = "Банковская карта"
		verbose_name_plural = "Банковские карты"
		ordering = ['-added']


class Payment(models.Model):
	PAYMENT_STATUS_CHOICES = [
		('pending', 'В ожидании'),
		('success', 'Успешно'),
		('failed', 'Неудачно'),
	]

	user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
	product_pocket = models.ForeignKey(ProductPocket, on_delete=models.CASCADE, verbose_name="Товар", null=True,
	                                   blank=True)
	order_id = models.CharField(max_length=255, verbose_name="Номер заказа", null=True, blank=True)
	card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Карта")
	amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма", null=True, blank=True)
	status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Статус",
	                          null=True, blank=True)
	created = models.DateTimeField(auto_now_add=True, verbose_name="Дата оплаты", null=True, blank=True)

	objects = models.Manager()

	def __str__(self):
		return f"{self.user} — {self.amount}({self.status})"

	class Meta:
		verbose_name = "Платёж"
		verbose_name_plural = "Платежи"
		ordering = ['-created']
