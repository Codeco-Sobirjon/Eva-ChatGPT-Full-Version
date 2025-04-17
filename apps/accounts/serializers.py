from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, ValidationError


class GroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'placeholder': 'Введите пароль'})
    password_confirm = serializers.CharField(write_only=True, required=True,
                                             style={'placeholder': 'Введите повторение пароль'})

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password', 'password_confirm', 'is_agree']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise ValidationError({"password_confirm": "Пароли не совпадают"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)

        groups_data = get_object_or_404(Group, id=1)

        user = get_user_model().objects.create_user(
            **validated_data
        )

        if groups_data:
            user.groups.set([groups_data])

        user.save()
        return user


class CustomAuthTokenSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'placeholder': 'Введите пароль'})

    def validate(self, data):
        identifier = data.get('identifier')
        password = data.get('password')

        if not identifier or not password:
            raise serializers.ValidationError("Телефон и пароль, оба поля обязательны")

        user_model = get_user_model()

        user = user_model.objects.filter(username=identifier).first()

        if user is None:
            raise AuthenticationFailed("Неверные данные, пользователь не найден")

        if not user.check_password(password):
            raise AuthenticationFailed("Неверные данные, неправильный пароль")

        return {
            'user': user,
        }


class CustomUserDetailSerializer(serializers.ModelSerializer):
    groups = GroupListSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'groups', 'avatar'
        ]



class PasswordUpdateSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)

    def update(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance
