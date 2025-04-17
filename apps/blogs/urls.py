from django.urls import path

from apps.blogs.views import BlogListCreateAPIView, BlogDetailAPIView

urlpatterns = [
	path('', BlogListCreateAPIView.as_view(), name='blog-list-create'),
	path('<int:pk>/', BlogDetailAPIView.as_view(), name='blog-detail'),
]
