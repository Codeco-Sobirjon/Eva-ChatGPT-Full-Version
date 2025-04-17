from django.urls import path

from apps.accounts.views import GoogleLoginAPIView, VKAuthAPIView, VKLogin, UserSignupView, CustomAuthTokenView, \
	CustomUserDetailView, PasswordUpdateView

urlpatterns = [
	path('auth/google/', GoogleLoginAPIView.as_view(), name='google-login'),
	path("auth/check/vk/", VKAuthAPIView.as_view(), name="vk-auth"),
    path('auth/vk/', VKLogin.as_view(), name='vk_login'),
	path('signup/', UserSignupView.as_view(), name='signup'),
    path('signin/', CustomAuthTokenView.as_view(), name='signin'),
    path('user/', CustomUserDetailView.as_view(), name='user-detail'),
	path('update-password/', PasswordUpdateView.as_view(), name='update-password'),
]
