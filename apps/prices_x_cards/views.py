from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ProductPocket, Card, Payment
from apps.prices_x_cards.serializers import ProductPocketSerializer, CardSerializer, \
	PaymentSerializer, PaymentDetailSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny, IsAuthenticated


class ProductListCreateAPIView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(responses={200: ProductPocketSerializer(many=True)}, tags=['Prices'])
	def get(self, request):
		products = ProductPocket.objects.all()
		serializer = ProductPocketSerializer(products, many=True)
		return Response(serializer.data)

	@swagger_auto_schema(request_body=ProductPocketSerializer, responses={201: ProductPocketSerializer()},
	                     tags=['Prices'])
	def post(self, request):
		serializer = ProductPocketSerializer(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(responses={200: ProductPocketSerializer()}, tags=['Prices'])
	def get(self, request, pk):
		try:
			product = ProductPocket.objects.get(pk=pk)
		except ProductPocket.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		serializer = ProductPocketSerializer(product)
		return Response(serializer.data)

	@swagger_auto_schema(request_body=ProductPocketSerializer, responses={200: ProductPocketSerializer()},
	                     tags=['Prices'])
	def put(self, request, pk):
		try:
			product = ProductPocket.objects.get(pk=pk)
		except ProductPocket.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		serializer = ProductPocketSerializer(product, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	@swagger_auto_schema(responses={204: 'No Content'}, tags=['Prices'])
	def delete(self, request, pk):
		try:
			product = ProductPocket.objects.get(pk=pk)
		except ProductPocket.DoesNotExist:
			return Response(status=status.HTTP_404_NOT_FOUND)
		product.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)


class CardListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
		tags=['Card'],
        operation_description="Получить список всех банковских карт",
        responses={200: CardSerializer(many=True)}
    )
    def get(self, request):
        cards = Card.objects.all()
        serializer = CardSerializer(cards, many=True, context={'request': request})
        return Response(serializer.data)

    @swagger_auto_schema(
		tags=['Card'],
        operation_description="Добавить новую банковскую карту",
        request_body=CardSerializer,
        responses={201: CardSerializer}
    )
    def post(self, request):
        serializer = CardSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
		tags=['Payment'],
        operation_summary="Получить список всех платежей",
        operation_description="Возвращает все платежи пользователей",
        responses={200: PaymentDetailSerializer(many=True)}
    )
    def get(self, request):
        payments = Payment.objects.all()
        serializer = PaymentDetailSerializer(payments, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
		tags=['Payment'],
        operation_summary="Создать новый платёж",
        operation_description="Создаёт новый платёж пользователя",
        request_body=PaymentSerializer,
        responses={201: PaymentSerializer}
    )
    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
