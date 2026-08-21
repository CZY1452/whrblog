from django.urls import path
from django.urls import re_path

from . import views
from .api_views import (
    AvatarUploadAPIView,
    ChangeEmailAPIView,
    ChangePasswordAPIView,
    ForgetPasswordAPIView,
    ForgetPasswordEmailCodeAPIView,
    LoginAPIView,
    LogoutAPIView,
    RegisterAPIView,
    UserInfoAPIView,
    VerifyEmailAPIView,
)

app_name = "accounts"

urlpatterns = [
    path(r'api/register',
         RegisterAPIView.as_view(),
         name='api-register'),
    path(r'api/login',
         LoginAPIView.as_view(),
         name='api-login'),
    path(r'api/logout',
         LogoutAPIView.as_view(),
         name='api-logout'),
    path(r'api/user',
         UserInfoAPIView.as_view(),
         name='api-user'),
    path(r'api/verify_email',
         VerifyEmailAPIView.as_view(),
         name='api-verify-email'),
    path(r'api/forget_password',
         ForgetPasswordAPIView.as_view(),
         name='api-forget-password'),
    path(r'api/forget_password_code',
         ForgetPasswordEmailCodeAPIView.as_view(),
         name='api-forget-password-code'),
    path(r'api/change_password',
         ChangePasswordAPIView.as_view(),
         name='api-change-password'),
    path(r'api/change_email',
         ChangeEmailAPIView.as_view(),
         name='api-change-email'),
    path(r'api/upload_avatar',
         AvatarUploadAPIView.as_view(),
         name='api-upload-avatar'),
    # 邮件链接跳回：改邮箱确认 → 跳转 SPA
    re_path(r'^change_email/(?P<id>\d+)/(?P<sign>[\w:-]+)\.html$',
            views.change_email_confirm,
            name='change_email_confirm'),
    # 邮件链接跳回：注册邮箱激活 → 服务端直接验证（兜底，无需 SPA 接管）
    path(r'verify-email',
         views.verify_email_confirm,
         name='verify_email_confirm'),
]