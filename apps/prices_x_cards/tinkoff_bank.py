import hashlib
import json
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
from apps.prices_x_cards.models import ProductPocket, Payment, Card


class TbankInitPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    TERMINAL_KEY = "1745327712798"
    PASSWORD = "VxMqwnk8t7xOJ!2E"
    # TERMINAL_KEY = "1745327712776DEMO"
    # PASSWORD = "9KlOjAkC^rgfG7Gl"
    INIT_URL = "https://securepay.tinkoff.ru/v2/Init"

    def generate_token(self, data, password):
        token_data = data.copy()
        token_data["Password"] = password
        token_data.pop("Token", None)
        token_data.pop("Receipt", None)
        sorted_items = sorted(token_data.items())
        token_string = "".join(str(v) for _, v in sorted_items)
        return hashlib.sha256(token_string.encode()).hexdigest()

    @swagger_auto_schema(
        operation_description="Инициализация платежа через Tinkoff для выбранного продукта.",
        manual_parameters=[
            openapi.Parameter(
                name="id",
                in_=openapi.IN_PATH,
                description="ID продукта (ProductPocket)",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешная инициализация платежа",
                examples={
                    "application/json": {
                        "order_id": "example-order-id",
                        "payment_url": "https://securepay.tinkoff.ru/v2/...",
                        "payment_id": 12345678
                    }
                }
            ),
            400: openapi.Response(
                description="Ошибка запроса",
                examples={
                    "application/json": {
                        "detail": "ID продукта не передан"
                    }
                }
            ),
            500: openapi.Response(
                description="Ошибка при запросе к Tinkoff API",
                examples={
                    "application/json": {
                        "error": "requests.exceptions.ConnectionError"
                    }
                }
            ),
        }
    )
    def post(self, request, *args, **kwargs):
        product_id = kwargs.get("id")
        if not product_id:
            return Response({"detail": "ID продукта не передан"}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(ProductPocket, id=product_id)
        order_id = str(uuid.uuid4())

        customer_key = None
        if request.user.is_authenticated:
            customer_key = str(request.user.id)
        else:
            customer_key = str(uuid.uuid4())

        amount = int(product.price * 100)

        receipt = {
            "Email": "no-reply@example.com",
            "Phone": "",
            "Taxation": "osn",
            "Items": [
                {
                    "Name": product.title,
                    "Price": amount,
                    "Quantity": 1.0,
                    "Amount": amount,
                    "PaymentMethod": "full_prepayment",
                    "PaymentObject": "commodity",
                    "Tax": "none"
                }
            ]
        }

        data = {
            "TerminalKey": self.TERMINAL_KEY,
            "Amount": int(product.price * 100),
            "OrderId": order_id,
            "Description": f"Оплата за продукт: {product.title}",
            "SuccessURL": "https://askeva.ru/blog",
            "FailURL": "https://askeva.ru/",
            "CustomerKey": customer_key,
            "Receipt": receipt
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
                    "customer_key": customer_key,
                    "payment_url": result.get("PaymentURL"),
                    "payment_id": result.get("PaymentId"),
                }, status=status.HTTP_200_OK)

            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        except requests.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckPaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]
    TERMINAL_KEY = "1745327712798"
    PASSWORD = "VxMqwnk8t7xOJ!2E"
    GET_STATE_URL = "https://securepay.tinkoff.ru/v2/GetState"
    GET_CARD_LIST_URL = "https://securepay.tinkoff.ru/v2/GetCardList"

    def generate_token(self, data: dict) -> str:
        print("🔐 Generating token...")
        data_for_token = data.copy()
        data_for_token.pop("Token", None)
        data_for_token["Password"] = self.PASSWORD

        for key, value in data_for_token.items():
            if isinstance(value, (dict, list)):
                data_for_token[key] = json.dumps(value, separators=(",", ":"), ensure_ascii=False)

        sorted_items = sorted(data_for_token.items())
        token_string = ''.join(str(v) for _, v in sorted_items)
        print(f"🔐 Token string: {token_string}")
        token = hashlib.sha256(token_string.encode('utf-8')).hexdigest()
        print(f"🔐 Generated token: {token}")

        return token

    def get_card_details(self, customer_key: str) -> dict:
        """Получение данных карты через GetCardList."""
        print(f"💳 Getting card details for CustomerKey: {customer_key}")
        data = {
            "TerminalKey": self.TERMINAL_KEY,
            "CustomerKey": customer_key,
        }
        print(f"💳 Card request data before token: {data}")
        data["Token"] = self.generate_token(data)
        print(f"💳 Card request data with token: {data}", data["Token"])
        try:
            print(f"📤 Sending POST request to {self.GET_CARD_LIST_URL}")
            response = requests.post(self.GET_CARD_LIST_URL, json=data)
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response body: {response.text}")
            response.raise_for_status()
            result = response.json()
            print(f"✅ Parsed card list response: {result}")
            return result
        except requests.RequestException as e:
            print(f"❌ Tinkoff API error: {str(e)}")
            return {"error": f"Ошибка Tinkoff API: {str(e)}"}
        except json.JSONDecodeError:
            print("❌ JSON decode error in card list response")
            return {"error": "Ответ Tinkoff не в формате JSON", "text": response.text}

    @swagger_auto_schema(
        operation_description="Проверка статуса платежа и получение данных карты клиента.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['payment_id', 'order_id', 'customer_key'],
            properties={
                'payment_id': openapi.Schema(type=openapi.TYPE_STRING, description="Идентификатор платежа"),
                'order_id': openapi.Schema(type=openapi.TYPE_STRING, description="Идентификатор заказа"),
                'customer_key': openapi.Schema(type=openapi.TYPE_STRING, description="Ключ клиента для получения данных карты"),
            },
        ),
    )
    def post(self, request, *args, **kwargs):
        print("📩 Incoming request data:", request.data)

        payment_id = request.data.get("payment_id")
        order_id = request.data.get("order_id")
        customer_key = request.data.get("customer_key")

        if not payment_id:
            return Response({"detail": "Требуется идентификатор платежа"}, status=400)
        if not order_id:
            return Response({"detail": "Требуется идентификатор заказа"}, status=400)
        if not customer_key:
            return Response({"detail": "Требуется ключ клиента"}, status=400)

        data = {
            "TerminalKey": self.TERMINAL_KEY,
            "PaymentId": str(payment_id),
        }
        print("📦 GetState request data before token:", data)
        data["Token"] = self.generate_token(data)

        card_list_response = self.get_card_details(customer_key)
        print("📋 Card list response:", card_list_response)

        try:
            print(f"📤 Sending POST request to {self.GET_STATE_URL}")
            response = requests.post(self.GET_STATE_URL, json=data)
            print(f"📥 GetState response status: {response.status_code}")
            print(f"📥 GetState response body: {response.text}")
            response.raise_for_status()
            result = response.json()
            print("✅ Parsed GetState response:", result)
        except requests.RequestException as e:
            print("❌ Tinkoff API error (GetState):", str(e))
            return Response({"detail": f"Ошибка Tinkoff API: {str(e)}"}, status=500)
        except json.JSONDecodeError as e:
            print("❌ JSON decode error in GetState response")
            return Response({
                "detail": "Ответ Tinkoff не в формате JSON",
                "status_code": response.status_code,
                "text": response.text
            }, status=500)

        if not result.get("Success"):
            print("❗ Payment not successful:", result)
            try:
                updated_payment = get_object_or_404(Payment, order_id=order_id)
                updated_payment.status = 'failed'
                updated_payment.save()
                print("📉 Payment status set to 'failed'")
            except Exception as e:
                print("❌ Error updating payment status to 'failed':", str(e))
                return Response({
                    "detail": "Ошибка при обновлении статуса платежа",
                    "error": str(e)
                }, status=500)

            return Response({
                "detail": result.get("Message"),
                "status": result.get("Status"),
                "error": result.get("Details")
            }, status=400)

        card_details = {}
        if customer_key:
            card_list_response = self.get_card_details(customer_key)
            print("📋 Card list response:", card_list_response)
            if "error" not in card_list_response:
                if card_list_response:
                    card = card_list_response[0]
                    card_details = {
                        "card_pan": card.get("Pan"),
                        "card_type": card.get("CardType"),
                        "card_exp_date": card.get("ExpDate"),
                    }
                    print("💾 Creating Card object in DB")
                    card = Card.objects.create(
                        user=request.user,
                        card_number=card.get("Pan"),
                        expiry_date=card.get("ExpDate"),
                        cardholder_name=card.get("CardHolder")
                    )

                    payment = get_object_or_404(Payment, order_id=order_id)
                    payment.card = card
                    payment.status = 'success'
                    payment.save()
                    print("✅ Payment updated with card and marked 'success'")
                else:
                    card_details = {"detail": "Карты для этого клиента не найдены"}
            else:
                card_details = {"detail": card_list_response["error"]}

        try:
            updated_payment = get_object_or_404(Payment, order_id=order_id)
            updated_payment.status = 'success'
            updated_payment.save()
            print("✅ Final payment status saved as 'success'")

            request_count = RequestCount.objects.create(
                user=request.user,
                is_active=True
            )
            print("📊 RequestCount record created")
        except Exception as e:
            print("❌ DB error while saving payment/request count:", str(e))
            return Response({
                "detail": f"Ошибка базы данных: {str(e)}"
            }, status=500)

        response_data = {
            "status": result.get("Status"),
            "amount": result.get("Amount"),
            "payment_id": result.get("PaymentId"),
            "card_pan": card_details.get("card_pan", None),
            "card_type": card_details.get("card_type", None),
            "card_exp_date": card_details.get("card_exp_date", None)
        }

        print("📤 Sending final response:", response_data)
        return Response(response_data)

