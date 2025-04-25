import hashlib
import requests
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.chat.models import RequestCount
from apps.prices_x_cards.models import ProductPocket, Payment


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

    def generate_token(self, data, password):
        token_data = data.copy()
        token_data["Password"] = password
        token_data.pop("Token", None)
        sorted_items = sorted(token_data.items())
        token_string = "".join(str(v) for _, v in sorted_items)
        return hashlib.sha256(token_string.encode()).hexdigest()

    def post(self, request, *args, **kwargs):
        payment_id = kwargs.get("payment_id")
        order_id = kwargs.get("order_id")

        if not payment_id:
            return Response({"detail": "Payment ID kerak"}, status=400)

        terminal_key = "1745327712776DEMO"
        password = "9KlOjAkC^rgfG7Gl"

        data = {
            "TerminalKey": terminal_key,
            "PaymentId": str(payment_id),
        }
        data["Token"] = self.generate_token(data, password)

        response = requests.post("https://securepay.tinkoff.ru/v2/GetState", json=data)
        result = response.json()

        if not result.get("Success"):
            updated_payment = get_object_or_404(Payment, order_id=order_id)
            updated_payment.status = 'failed'
            updated_payment.save()

            return Response({
                "detail": result.get("Message"),
                "status": result.get("Status"),
                "error": result.get("Details")
            }, status=400)

        updated_payment = get_object_or_404(Payment, order_id=order_id)
        updated_payment.status = 'success'
        updated_payment.save()

        request_count = RequestCount.objects.create(
            user=request.user, is_active=True
        )

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
