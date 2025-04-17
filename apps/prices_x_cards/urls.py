from django.urls import path
from apps.prices_x_cards.views import ProductListCreateAPIView, ProductDetailAPIView, \
    CardListCreateAPIView, PaymentListCreateAPIView

urlpatterns = [
    path('', ProductListCreateAPIView.as_view(), name='product-list-create'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('card/', CardListCreateAPIView.as_view(), name='card'),
    path('payments/', PaymentListCreateAPIView.as_view(), name='payment-list-create'),
]