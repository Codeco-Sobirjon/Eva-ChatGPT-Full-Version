from rest_framework import serializers

from apps.accounts.serializers import CustomUserDetailSerializer
from apps.chat.models import ChatHistory, RequestCount
from apps.prices_x_cards.models import ProductPocket, Card, Payment


class ProductPocketSerializer(serializers.ModelSerializer):
    price_digits = serializers.ReadOnlyField()

    class Meta:
        model = ProductPocket
        fields = ['id', 'title', 'description', 'price', 'price_type', 'price_digits', 'count_typing']


class CardSerializer(serializers.ModelSerializer):
    user = CustomUserDetailSerializer(read_only=True)

    class Meta:
        model = Card
        fields = ['id', 'user', 'card_number', 'expiry_date', 'cardholder_name', 'added']

    def create(self, validated_data):
        create = Card.objects.create(**validated_data)
        create.user = self.context['request'].user
        create.save()
        return create


class CardCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['card_number', 'expiry_date', 'cardholder_name']


class PaymentSerializer(serializers.ModelSerializer):

    card = CardCreateSerializer()

    class Meta:
        model = Payment
        fields = ['id', 'user', 'product_pocket', 'card', 'amount', 'status', 'created', 'card']
        read_only_fields = ['user', 'status', 'created']

    def create(self, validated_data):
        user = self.context.get('request').user
        card_data = validated_data.pop('card')
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'pending'

        create_card = Card.objects.create(user=user, **card_data)

        create_payment = Payment.objects.create(**validated_data, card=create_card)

        request_count = RequestCount.objects.create(
            user=user, is_active=True
        )
        return create_payment


class PaymentDetailSerializer(PaymentSerializer):
    user = CustomUserDetailSerializer(read_only=True)
    product_pocket = ProductPocketSerializer(read_only=True)
    card = CardSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'user', 'product_pocket', 'card', 'amount', 'status', 'created']
