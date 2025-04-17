from rest_framework import serializers

from django.db import transaction

from apps.blogs.models import (
	Blog, BlogImage, BlogViews
)


class BlogImageSerializer(serializers.ModelSerializer):
	class Meta:
		model = BlogImage
		fields = ['id', 'image']


class BlogSerializer(serializers.ModelSerializer):
	images = BlogImageSerializer(many=True, required=False)
	status = serializers.ChoiceField(choices=Blog.BlogStatus.choices, required=False)

	class Meta:
		model = Blog
		fields = ['id', 'title', 'description', 'status', 'created_at', 'images']

	def create(self, validated_data):
		request = self.context.get('request')
		images_data = request.FILES.getlist('images') if request else []

		blog = Blog.objects.create(
			title=validated_data.get('title'),
			description=validated_data.get('description'),
			status=validated_data.get('status', Blog.BlogStatus.INACTIVE)
		)

		for image in images_data:
			BlogImage.objects.create(blog=blog, image=image)

		return blog

	def update(self, instance, validated_data):
		instance.title = validated_data.get('title', instance.title)
		instance.description = validated_data.get('description', instance.description)
		instance.status = validated_data.get('status', instance.status)
		instance.save()

		request = self.context.get('request')
		if request and request.FILES.getlist('images'):
			instance.images.all().delete()
			for image in request.FILES.getlist('images'):
				BlogImage.objects.create(blog=instance, image=image)

		return instance


class BlogViewsSerializer(serializers.ModelSerializer):
	class Meta:
		model = BlogViews
		fields = ['id', 'blog', 'user', 'last_viewed_at']
