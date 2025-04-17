from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.db import models
from apps.accounts.managers.custom_user import CustomUserManager
from django.utils.translation import gettext as _
from django.conf import settings


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name="Электронная почта", null=True, blank=True)
    username = models.CharField(max_length=250, unique=True, verbose_name="Логин", null=True, blank=True)
    first_name = models.CharField(max_length=30, verbose_name="Имя", null=True, blank=True)
    last_name = models.CharField(max_length=30, verbose_name="Фамилия", null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name=_("Аватар"))
    about_yourself = models.TextField(null=True, blank=True, verbose_name="О себе")
    birth_date = models.DateField(null=True, blank=True, verbose_name="День рождения")
    is_agree = models.BooleanField(null=True, blank=True, default=False, verbose_name="Чекбокс согласие на условия")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Персонал")

    groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True, verbose_name="Группы")
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_set", blank=True,
                                              verbose_name="Разрешения")

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

