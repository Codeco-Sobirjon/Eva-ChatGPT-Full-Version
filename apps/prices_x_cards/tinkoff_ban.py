# views.py
import hashlib
import json
import requests
from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response


class CreateTinkoffPaymentView(APIView):
	permission_classes = [AllowAny]


	def post(self, request):
		order_id = 'TESTORDER123'  # In real use, generate dynamic ID

		payload = {
			"TerminalKey": settings.TINKOFF_TERMINAL_KEY,
			"Amount": settings.TINKOFF_AMOUNT,
			"OrderId": order_id,
			"Description": "Static test payment",
			"SuccessURL": "https://yourdomain.com/payment-success/",
		}

		# Generate token
		token_data = payload.copy()
		token_data["Password"] = settings.TINKOFF_PASSWORD
		sorted_items = sorted(token_data.items())
		token_string = ''.join(str(v) for _, v in sorted_items)
		payload["Token"] = hashlib.sha256(token_string.encode()).hexdigest()

		response = requests.post(
			"https://securepay.tinkoff.ru/v2/Init",
			data=json.dumps(payload),
			headers={"Content-Type": "application/json"}
		)

		result = response.json()
		if result.get("Success"):
			return Response({"url": result["PaymentURL"]})
		return Response(result, status=400)
