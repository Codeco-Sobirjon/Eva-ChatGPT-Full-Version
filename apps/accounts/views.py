from urllib.parse import urlparse, parse_qs

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from apps.accounts.services import GoogleLoginService
import requests
from apps.accounts.serializers import (
    SignUpSerializer, CustomAuthTokenSerializer, CustomUserDetailSerializer,
    PasswordUpdateSerializer
)

User = get_user_model()

USER_FIELDS = [
	"first_name", "last_name", "nickname", "screen_name", "sex", "bdate", "city",
	"country", "timezone", "photo", "photo_medium", "photo_big", "photo_max_orig",
	"has_mobile", "contacts", "education", "online", "counters", "relation",
	"last_seen", "activity", "universities",
]


class GoogleLoginAPIView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(
		operation_summary="Google OAuth2 Authentication URL",
		operation_description="This endpoint returns the URL to begin the Google OAuth2 authentication process.",
		responses={
			200: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"auth_url": openapi.Schema(type=openapi.TYPE_STRING,
					                           description="URL to authenticate via Google OAuth2."),
				}
			),
		}
	)
	def get(self, request):

		google_service = GoogleLoginService()
		auth_url = google_service.get_authorization_url()
		return Response({"auth_url": auth_url}, status=status.HTTP_200_OK)

	@swagger_auto_schema(
		operation_summary="Exchange Code for Tokens",
		operation_description="This endpoint exchanges the Google OAuth2 authorization code for access and refresh tokens.",
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			properties={
				"code": openapi.Schema(type=openapi.TYPE_STRING,
				                       description="The authorization code from Google OAuth2."),
			},
			required=["code"]
		),
		responses={
			200: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"access_token": openapi.Schema(type=openapi.TYPE_STRING, description="JWT access token."),
					"refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="JWT refresh token."),
				}
			),
			400: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"error": openapi.Schema(type=openapi.TYPE_STRING, description="Description of the error."),
				}
			),
		}
	)
	def post(self, request):
		code = request.data.get('code')
		if not code:
			return Response({"error": "Authorization code missing"}, status=status.HTTP_400_BAD_REQUEST)

		google_service = GoogleLoginService()
		tokens = google_service.get_tokens(code)
		if 'access_token' not in tokens:
			return Response({"error": "Failed to retrieve tokens"}, status=status.HTTP_400_BAD_REQUEST)

		user_info = google_service.get_user_info(tokens['access_token'])

		user = google_service.create_or_get_user(user_info)

		access_token, refresh_token = google_service.get_jwt_token(user)

		return Response({
			"access_token": access_token,
			"refresh_token": refresh_token
		}, status=status.HTTP_200_OK)


class VKSignInURLAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['VK'],
        operation_summary="Получение URL для входа через VK",
        operation_description="Этот эндпоинт возвращает URL для авторизации через VK.",
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "sign_in_url": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description="URL для входа через VK."
                    )
                }
            )
        }
    )
    def get(self, request):
        client_id = "52982778"
        redirect_uri = "https://askeva.ru/auth/vk/login/callback/"
        scope = "email"
        response_type = "code"
        v = "5.131"

        sign_in_url = (
            f"https://oauth.vk.com/authorize?"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope={scope}&"
            f"response_type={response_type}&"
            f"v={v}"
        )

        return Response({"sign_in_url": sign_in_url}, status=200)


class VKAuthAPIView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(
		tags=['VK'],
		operation_summary="Получение access_token от VK",
		operation_description="Этот эндпоинт принимает callback_url, извлекает code и получает access_token от VK API.",
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			properties={
				"callback_url": openapi.Schema(
					type=openapi.TYPE_STRING,
					description="URL с кодом авторизации VK, полученным после логина."
				)
			},
			required=["callback_url"]
		),
		responses={
			200: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"access_token": openapi.Schema(
						type=openapi.TYPE_STRING,
						description="Токен доступа VK."
					)
				}
			),
			400: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"error": openapi.Schema(
						type=openapi.TYPE_STRING,
						description="Описание ошибки."
					)
				}
			),
		}
	)
	def post(self, request):
		callback_url = request.data.get("callback_url")

		if not callback_url:
			return Response({"error": "callback_url is required"}, status=status.HTTP_400_BAD_REQUEST)

		parsed_url = urlparse(callback_url)
		query_params = parse_qs(parsed_url.query)
		code = query_params.get("code", [None])[0]

		if not code:
			return Response({"error": "Authorization code not found"}, status=status.HTTP_400_BAD_REQUEST)

		token_url = (
			f"https://oauth.vk.com/access_token?"
			f"client_id=52982778&"
			f"client_secret=tPZ6YRgnZzwubzWy7RyF&"
			f"redirect_uri=https://askeva.ru/auth/vk/login/callback/&"
			f"code={code}"
		)

		response = requests.get(token_url)

		if response.status_code == 200:
			data = response.json()
			access_token = data.get("access_token")

			if not access_token:
				return Response({"error": "access_token not found"}, status=status.HTTP_400_BAD_REQUEST)

			return Response({"access_token": access_token}, status=status.HTTP_200_OK)
		else:
			return Response(
				{"error": "Failed to get access token", "details": response.text},
				status=response.status_code,
			)


class VKLogin(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(
		tags=['VK'],
		operation_summary="Аутентификация через VK",
		operation_description="Получает `access_token` VK, запрашивает профиль пользователя и возвращает JWT токены.",
		request_body=openapi.Schema(
			type=openapi.TYPE_OBJECT,
			properties={
				"access_token": openapi.Schema(
					type=openapi.TYPE_STRING,
					description="VK access token, полученный после авторизации."
				)
			},
			required=["access_token"]
		),
		responses={
			200: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"access_token": openapi.Schema(
						type=openapi.TYPE_STRING,
						description="JWT access token."
					),
					"refresh_token": openapi.Schema(
						type=openapi.TYPE_STRING,
						description="JWT refresh token."
					),
					"user_data": openapi.Schema(
						type=openapi.TYPE_OBJECT,
						description="Данные пользователя VK.",
						properties={
							"id": openapi.Schema(type=openapi.TYPE_INTEGER, description="VK ID пользователя."),
							"first_name": openapi.Schema(type=openapi.TYPE_STRING, description="Имя."),
							"last_name": openapi.Schema(type=openapi.TYPE_STRING, description="Фамилия."),
							"photo_max_orig": openapi.Schema(type=openapi.TYPE_STRING, description="URL аватара.")
						}
					)
				}
			),
			400: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"error": openapi.Schema(type=openapi.TYPE_STRING, description="Описание ошибки.")
				}
			),
			500: openapi.Schema(
				type=openapi.TYPE_OBJECT,
				properties={
					"error": openapi.Schema(type=openapi.TYPE_STRING, description="Ошибка на сервере.")
				}
			),
		}
	)
	def post(self, request, *args, **kwargs):
		data = request.data
		access_token = data.get("access_token")

		if not access_token:
			return Response({"error": "Access token is required"}, status=status.HTTP_400_BAD_REQUEST)

		profile_url = "https://api.vk.com/method/users.get"
		params = {
			"v": "5.131",
			"access_token": access_token,
			"fields": ",".join(USER_FIELDS),
		}

		try:
			response = requests.get(profile_url, params=params)
			response.raise_for_status()
			user_data = response.json().get("response", [{}])[0]

			if not user_data:
				return Response({"error": "No user data found"}, status=status.HTTP_404_NOT_FOUND)

			vk_id = user_data.get("id")
			first_name = user_data.get("first_name", "")
			last_name = user_data.get("last_name", "")
			bdate = user_data.get("bdate", "")
			photo_url = user_data.get("photo_max_orig", "")

			username = f"vk_{vk_id}"

			user, created = User.objects.get_or_create(username=username, defaults={
				"first_name": first_name,
				"last_name": last_name,
				'birth_date': datetime.strptime(bdate, "%d.%m.%Y").date() if bdate else None,
			})

			if photo_url:
				photo_response = requests.get(photo_url)
				if photo_response.status_code == 200:
					avatar_name = f"avatars/{username}.jpg"
					user.avatar.save(avatar_name, ContentFile(photo_response.content), save=True)

			refresh = RefreshToken.for_user(user)
			access_token = str(refresh.access_token)

			return Response({
				"access_token": access_token,
				"refresh_token": str(refresh)
			}, status=status.HTTP_200_OK)

		except requests.exceptions.RequestException as e:
			return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomAuthTokenView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(request_body=CustomAuthTokenSerializer, tags=['Account'])
	def post(self, request):
		serializer = CustomAuthTokenSerializer(data=request.data)

		if serializer.is_valid():
			user = serializer.validated_data['user']
			refresh = RefreshToken.for_user(user)

			return Response({
				'refresh': str(refresh),
				'access': str(refresh.access_token),
			}, status=status.HTTP_200_OK)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserSignupView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(request_body=SignUpSerializer, tags=['Account'])
	def post(self, request, *args, **kwargs):
		serializer = SignUpSerializer(data=request.data)
		if serializer.is_valid():
			user = serializer.save()
			return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomAuthTokenView(APIView):
	permission_classes = [AllowAny]

	@swagger_auto_schema(request_body=CustomAuthTokenSerializer, tags=['Account'])
	def post(self, request):
		serializer = CustomAuthTokenSerializer(data=request.data)

		if serializer.is_valid():
			user = serializer.validated_data['user']
			refresh = RefreshToken.for_user(user)

			return Response({
				'refresh': str(refresh),
				'access': str(refresh.access_token),
			}, status=status.HTTP_200_OK)

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomUserDetailView(APIView):
	permission_classes = [IsAuthenticated]

	@swagger_auto_schema(
		responses={200: CustomUserDetailSerializer()},
		operation_description="Retrieve details of the authenticated user.", tags=['Account']
	)
	def get(self, request):
		user = request.user
		serializer = CustomUserDetailSerializer(user, context={'request': request})
		return Response(serializer.data, status=status.HTTP_200_OK)

	@swagger_auto_schema(
		responses={204: 'No Content'},
		operation_description="Delete the authenticated user's account.", tags=['Account']
	)
	def delete(self, request):
		user = request.user
		user.delete()
		return Response({"detail": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class CustomUserView(APIView):
	permission_classes = [IsAuthenticated]

	@swagger_auto_schema(
		responses={200: CustomUserDetailSerializer()},
		operation_description="Retrieve details of the guest user.", tags=['Account']
	)
	def get(self, request, *args, **kwargs):
		user_model = get_user_model()
		user = get_object_or_404(user_model, id=kwargs.get('id'))
		serializer = CustomUserDetailSerializer(user, context={'request': request})
		return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordUpdateView(APIView):
	permission_classes = [IsAuthenticated]

	@swagger_auto_schema(
		request_body=PasswordUpdateSerializer,
		tags=['Account'],
		responses={
			200: "Password updated successfully.",
			400: "Bad Request: Password update failed."
		},
		operation_description="Update the authenticated user's password."
	)
	def patch(self, request):
		serializer = PasswordUpdateSerializer(data=request.data, context={'request': request})
		if serializer.is_valid():
			serializer.update(request.user, serializer.validated_data)
			return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordUpdateViews(APIView):
	permission_classes = [IsAuthenticated]

	pass