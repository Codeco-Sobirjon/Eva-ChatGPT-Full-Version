import requests
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import CustomUser


class GoogleLoginService:
    AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def get_authorization_url(self):
        print(settings.GOOGLE_REDIRECT_URI)
        print(settings.GOOGLE_CLIENT_ID)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        auth_url = f"{self.AUTH_URL}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        return auth_url

    def get_tokens(self, code):
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        response = requests.post(self.TOKEN_URL, data=data)
        return response.json()

    def get_user_info(self, access_token):
        response = requests.get(self.USER_INFO_URL, params={"access_token": access_token})
        return response.json()

    def create_or_get_user(self, user_info):
        try:
            user = CustomUser.objects.get(email=user_info['email'])
        except ObjectDoesNotExist:
            user = CustomUser.objects.create(
                email=user_info['email'],
                first_name=user_info.get('given_name', ''),
                last_name=user_info.get('family_name', ''),
                username=user_info['email'],
                is_active=True,
            )
        return user

    def get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        return access_token, str(refresh)
