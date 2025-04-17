from django.contrib import admin
from apps.prices_x_cards.models import ProductPocket, Card, Payment


@admin.register(ProductPocket)
class ProductPocketAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'price_type', 'count_typing', 'price_digits')
    list_filter = ('price_type',)
    search_fields = ('title', 'description')
    readonly_fields = ('price_digits',)

    def price_digits(self, obj):
        return obj.price_digits
    price_digits.short_description = 'Цифр в цене'


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('user', 'masked_card_number', 'expiry_date', 'cardholder_name', 'added')
    list_filter = ('added',)
    search_fields = ('user__username', 'card_number', 'cardholder_name')

    def masked_card_number(self, obj):
        return f"**** **** **** {obj.card_number[-4:]}"
    masked_card_number.short_description = 'Номер карты'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_pocket', 'card', 'amount', 'status', 'created')
    list_filter = ('status', 'created', 'card', 'product_pocket')
    search_fields = ('user__username', 'user__email', 'product_pocket__product__title', 'card__number')
    autocomplete_fields = ('user', 'product_pocket', 'card')
    readonly_fields = ('created',)
    ordering = ('-created',)

    fieldsets = (
        (None, {
            'fields': ('user', 'product_pocket', 'card', 'amount', 'status')
        }),
        ('Дополнительно', {
            'fields': ('created',),
            'classes': ('collapse',),
        }),
    )