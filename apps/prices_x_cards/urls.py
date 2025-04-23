from django.urls import path

from apps.prices_x_cards.tinkoff_ban import CreateTinkoffPaymentView
from apps.prices_x_cards.views import ProductListCreateAPIView, ProductDetailAPIView, \
    CardListCreateAPIView, PaymentListCreateAPIView
from apps.prices_x_cards.yukassa import (GetPaymentUrlRobokassa)
                                         # PaymentSuccess, PaymentFail, PaymentResult

urlpatterns = [
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('card/', CardListCreateAPIView.as_view(), name='card'),
    path('payments/', PaymentListCreateAPIView.as_view(), name='payment-list-create'),
    path('get_payment_url_robokassa/', GetPaymentUrlRobokassa.as_view(), name='get_payment_url'),
    # path('payment/success/', PaymentSuccess.as_view(), name='payment_success'),
    # path('payment/fail/', PaymentFail.as_view(), name='payment_fail'),
    # path('payment/result/', PaymentResult.as_view(), name='payment_result'),
    path('api/pay/', CreateTinkoffPaymentView.as_view(), name='create-payment'),
]