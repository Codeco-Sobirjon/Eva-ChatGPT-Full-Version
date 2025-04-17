from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import CustomUser
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib.sites.models import Site


class CustomUserAdmin(UserAdmin):
	def group_names(self, obj):
		return ", ".join([group.name for group in obj.groups.all()])

	group_names.short_description = 'Рол'

	def avatar_preview(self, obj):
		if obj.avatar:
			return mark_safe(f'<img src="{obj.avatar.url}" width="75" height="75" />')
		return "No Avatar"

	avatar_preview.short_description = 'Аватар'

	model = CustomUser
	list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'group_names', 'avatar_preview')
	readonly_fields = ['avatar_preview']

	fieldsets = (
		(None, {'fields': ('username', 'password', 'avatar')}),
		('Персональная информация',
		 {'fields': ('first_name', 'last_name', 'birth_date', 'email', 'about_yourself')}),
		('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
		('Группы и права', {'fields': ('groups', 'user_permissions')}),
	)

	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': (
				'username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'avatar',
				'about_yourself', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'birth_date'
			),
		}),
	)

	search_fields = ('username', 'first_name', 'last_name', 'email')
	ordering = ('id',)


admin.site.register(CustomUser, CustomUserAdmin)
