# E802VhP4wJVuT6XrHIBd
# ry4jUB1x00NbQWGFDYq6

import uuid
import hashlib
import json
from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@method_decorator(csrf_exempt, name='dispatch')
class GetPaymentUrlRobokassa(View):
    def post(self, request):
        try:
            data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        amount = data.get('amount')
        description = data.get('description', 'Payment via Robokassa')

        if not amount:
            return JsonResponse({'error': 'Amount is required'}, status=400)

        try:
            amount = str(float(amount))  # Ensure it's a proper decimal string
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)

        inv_id = str(uuid.uuid4())
        sign_str = f"{settings.ROBOKASSA_SHOP_ID}:{amount}:{inv_id}:{settings.ROBOKASSA_SECRET_KEY}"
        signature = hashlib.md5(sign_str.encode()).hexdigest()

        params = {
            'MrchLogin': settings.ROBOKASSA_SHOP_ID,
            'OutSum': amount,
            'InvId': inv_id,
            'Desc': description,
            'SignatureValue': signature,
            'Culture': 'en',
            'Encoding': 'utf-8',
            'IsTest': 0,
            'SuccessURL': request.build_absolute_uri('/payment/success/'),
            'FailURL': request.build_absolute_uri('/payment/fail/'),
        }

        payment_url = f"{settings.ROBOKASSA_URL}?{urlencode(params)}"

        return JsonResponse({'payment_url': payment_url, 'inv_id': inv_id})