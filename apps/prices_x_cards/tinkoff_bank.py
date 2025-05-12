import hashlib
import json
import logging

import requests
import uuid

from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import RequestCount
from apps.prices_x_cards.models import ProductPocket, Payment


class TbankInitPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    TERMINAL_KEY = "1745327712776DEMO"
    PASSWORD = "9KlOjAkC^rgfG7Gl"
    INIT_URL = "https://securepay.tinkoff.ru/v2/Init"

    def generate_token(self, data, password):
        token_data = data.copy()
        token_data["Password"] = password
        token_data.pop("Token", None)
        sorted_items = sorted(token_data.items())
        token_string = "".join(str(v) for _, v in sorted_items)
        return hashlib.sha256(token_string.encode()).hexdigest()

    def post(self, request, *args, **kwargs):
        product_id = kwargs.get("id")
        if not product_id:
            return Response({"detail": "ID продукта не передан"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(ProductPocket, id=product_id)
        order_id = str(uuid.uuid4())

        data = {
            "TerminalKey": self.TERMINAL_KEY,
            "Amount": int(product.price * 100),
            "OrderId": order_id,
            "Description": f"Оплата за продукт: {product.title}",
            "SuccessURL": "https://example.com/success",
            "FailURL": "https://example.com/fail",
        }

        data["Token"] = self.generate_token(data, self.PASSWORD)

        try:
            response = requests.post(self.INIT_URL, json=data)
            result = response.json()

            if result.get("Success"):
                Payment.objects.create(
                    user=request.user,
                    product_pocket=product,
                    amount=product.price,
                    status="pending",
                    order_id=order_id
                )
                return Response({
                    "order_id": order_id,
                    "payment_url": result.get("PaymentURL"),
                    "payment_id": result.get("PaymentId"),
                }, status=status.HTTP_200_OK)

            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InitPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def generate_token(self, data, password):
        token_data = data.copy()
        token_data["Password"] = password
        token_data.pop("Token", None)

        sorted_items = sorted(token_data.items())
        token_string = "".join(str(v) for _, v in sorted_items)

        return hashlib.sha256(token_string.encode()).hexdigest()

    def post(self, request, *args, **kwargs):
        product_id = kwargs.get("id")
        if not product_id:
            return Response({"detail": "Mahsulot ID topilmadi"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(ProductPocket, id=product_id)

        terminal_key = "1745327712776DEMO"
        password = "9KlOjAkC^rgfG7Gl"
        order_id = f"{uuid.uuid4()}"

        data = {
            "TerminalKey": terminal_key,
            "Amount": int(product.price * 100),
            "OrderId": order_id,
            "Description": f"Для продукта: {product.title}"
        }

        data["Token"] = self.generate_token(data, password)

        response = requests.post("https://securepay.tinkoff.ru/v2/Init", json=data)
        result = response.json()

        if result.get("Success"):
            payment = Payment.objects.create(
                user=request.user,
                product_pocket=product,
                amount=product.price,
                status="pending",
                order_id=order_id
            )
            return Response({
                "order_id": order_id,
                "payment_url": result.get("PaymentURL"),
                "payment_id": result.get("PaymentId"),
            }, status=status.HTTP_200_OK)

        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class CheckPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    TERMINAL_KEY = "1745327712798"
    PASSWORD = "VxMqwnk8t7xOJ!2E"
    GET_STATE_URL = "https://securepay.tinkoff.ru/v2/GetState"

    def generate_token(self, data: dict) -> str:
        data_for_token = data.copy()
        data_for_token.pop("Token", None)
        data_for_token["Password"] = self.PASSWORD

        for key, value in data_for_token.items():
            if isinstance(value, (dict, list)):
                data_for_token[key] = json.dumps(value, separators=(",", ":"), ensure_ascii=False)

        sorted_items = sorted(data_for_token.items())
        token_string = ''.join(str(v) for _, v in sorted_items)
        token = hashlib.sha256(token_string.encode('utf-8')).hexdigest()

        return token

    def post(self, request, *args, **kwargs):
        payment_id = kwargs.get("payment_id")
        order_id = kwargs.get("order_id")

        if not payment_id:

            return Response({"detail": "Payment ID kerak"}, status=400)
        if not order_id:

            return Response({"detail": "Order ID kerak"}, status=400)

        data = {
            "TerminalKey": self.TERMINAL_KEY,
            "PaymentId": str(payment_id),
        }
        data["Token"] = self.generate_token(data)

        try:
            response = requests.post(self.GET_STATE_URL, json=data)
            response.raise_for_status()

            try:
                result = response.json()
            except json.JSONDecodeError as e:
                return Response({
                    "detail": "Tinkoff javobi JSON emas",
                    "status_code": response.status_code,
                    "text": response.text
                }, status=500)

        except requests.RequestException as e:
            return Response({
                "detail": f"Tinkoff API xatosi: {str(e)}"
            }, status=500)

        if not result.get("Success"):

            try:
                updated_payment = get_object_or_404(Payment, order_id=order_id)
                updated_payment.status = 'failed'
                updated_payment.save()
            except Exception as e:
                return Response({
                    "detail": "Payment statusini yangilashda xatolik",
                    "error": str(e)
                }, status=500)

            return Response({
                "detail": result.get("Message"),
                "status": result.get("Status"),
                "error": result.get("Details")
            }, status=400)

        try:
            updated_payment = get_object_or_404(Payment, order_id=order_id)
            updated_payment.status = 'success'
            updated_payment.save()

            request_count = RequestCount.objects.create(
                user=request.user,
                is_active=True
            )

        except Exception as e:
            return Response({
                "detail": f"Ma'lumotlar bazasi xatosi: {str(e)}"
            }, status=500)

        return Response({
            "status": result.get("Status"),
            "amount": result.get("Amount"),
            "payment_id": result.get("PaymentId"),
            "card_pan": result.get("Pan"),
            "card_type": result.get("CardType"),
            "card_exp_date": result.get("ExpDate"),
            "payment_url": result.get("PaymentURL"),
            "error": result.get("Details"),
        })
