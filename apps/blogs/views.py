from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from apps.blogs.models import Blog, BlogViews
from apps.blogs.serializers import BlogSerializer
from django.utils import timezone


class BlogPagination(PageNumberPagination):
	page_size = 8
	page_size_query_param = 'page_size'
	max_page_size = 100


class BlogListCreateAPIView(APIView):
	permission_classes = [IsAuthenticated]

	@swagger_auto_schema(
		tags=['Blogs'],
		operation_summary="Получить список блогов с пагинацией",
		responses={200: BlogSerializer(many=True)}
	)
	def get(self, request):
		blogs = Blog.objects.all().order_by('-created_at').filter(status=Blog.BlogStatus.ACTIVE)
		paginator = BlogPagination()
		result_page = paginator.paginate_queryset(blogs, request)
		serializer = BlogSerializer(result_page, many=True, context={'request': request})
		return paginator.get_paginated_response(serializer.data)

	@swagger_auto_schema(
		tags=['Blogs'],
		operation_summary="Создать новый блог",
		request_body=BlogSerializer,
		responses={201: BlogSerializer}
	)
	def post(self, request):
		serializer = BlogSerializer(data=request.data, context={'request': request})
		if serializer.is_valid():
			blog = serializer.save()
			return Response(BlogSerializer(blog).data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BlogDetailAPIView(APIView):
	permission_classes = [IsAuthenticated]

	@swagger_auto_schema(
		tags=['Blogs'],
		operation_summary="Получить конкретный блог по ID",
		responses={200: BlogSerializer}
	)
	def get(self, request, pk):
		try:
			blog = Blog.objects.get(pk=pk)
		except Blog.DoesNotExist:
			return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

		if request.user.is_authenticated:
			BlogViews.objects.update_or_create(
				blog=blog,
				user=request.user,
				defaults={'last_viewed_at': timezone.now()}
			)

		serializer = BlogSerializer(blog, context={'request': request})
		return Response(serializer.data)

	@swagger_auto_schema(
		tags=['Blogs'],
		operation_summary="Обновить блог по ID",
		request_body=BlogSerializer,
		responses={200: BlogSerializer}
	)
	def put(self, request, pk):
		try:
			blog = Blog.objects.get(pk=pk)
		except Blog.DoesNotExist:
			return Response({'error': 'Not Found'}, status=status.HTTP_404_NOT_FOUND)

		serializer = BlogSerializer(blog, data=request.data, context={'request': request})
		if serializer.is_valid():
			blog = serializer.save()
			return Response(BlogSerializer(blog).data)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	@swagger_auto_schema(
		tags=['Blogs'],
		operation_summary="Удалить блог по ID"
	)
	def delete(self, request, pk):
		try:
			blog = Blog.objects.get(pk=pk)
			blog.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except Blog.DoesNotExist:
			return Response({'error': 'Blog not found'}, status=status.HTTP_404_NOT_FOUND)
