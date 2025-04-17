from django.contrib import admin

from apps.blogs.models import (
	Blog, BlogImage
)


class BlogImageTableInlines(admin.TabularInline):
	model = BlogImage
	extra = 1


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
	list_display = ['id', 'title', 'created_at']
	inlines = [BlogImageTableInlines]
