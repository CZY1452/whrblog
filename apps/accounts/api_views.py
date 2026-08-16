import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core import signing as django_signing
from django.urls import reverse
from PIL import Image
from rest_framework import status, throttling
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BlogUser
from apps.accounts.serializers import (
    BlogUserSerializer,
    ChangePasswordSerializer,
    ChangeEmailSerializer,
    ForgetPasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
    UpdateProfileSerializer,
    VerifyEmailCodeSerializer,
)
from apps.accounts.utils import send_verify_email, set_code, verify
from core.utils import (
    delete_sidebar_cache,
    generate_code,
    get_current_site,
    get_sha256,
    send_email,
)

logger = logging.getLogger(__name__)


class RegisterAPIView(APIView):
    """用户注册（需邮箱验证激活）"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        site = get_current_site().domain
        if settings.DEBUG:
            site = '127.0.0.1:8000'
        sign = django_signing.dumps(
            {'user_id': user.id},
            salt='email-verify',
        )
        url = "http://{site}/verify-email?id={id}&sign={sign}".format(
            site=site, id=user.id, sign=sign)
        content = """
        <p>请点击下面链接验证您的邮箱</p>
        <a href="{url}" rel="bookmark">{url}</a>
        再次感谢您！
        <br />
        如果上面链接无法打开，请将此链接复制至浏览器。
        {url}
        """.format(url=url)
        send_email(emailto=[user.email], title='验证您的电子邮箱', content=content)

        return Response({
            'success': True,
            'message': '注册成功，请前往邮箱完成验证',
            'user': BlogUserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """用户登录"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if not user or not user.is_active:
            return Response({'error': '用户名或密码错误，或账号未激活'},
                            status=status.HTTP_400_BAD_REQUEST)

        login(request, user)
        delete_sidebar_cache()

        if serializer.validated_data.get('remember'):
            request.session.set_expiry(settings.REMEMBER_ME_LOGIN_TTL)
        else:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)

        response = Response({
            'success': True,
            'user': BlogUserSerializer(user).data,
        })
        response.set_cookie(
            'logged_user',
            value='true',
            max_age=settings.SESSION_COOKIE_AGE,
            httponly=True,
            samesite='Lax',
        )
        return response


class VerifyEmailAPIView(APIView):
    """邮箱激活验证（注册邮件链接指向 SPA /verify-email，SPA 调用此接口）"""
    permission_classes = [AllowAny]

    def post(self, request):
        user_id = request.data.get('id')
        sign = request.data.get('sign')
        if not user_id or not sign:
            return Response({'error': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        user = BlogUser.objects.filter(pk=user_id).first()
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        if user.is_active:
            return Response({'success': True, 'message': '账号已激活'})
        try:
            data = django_signing.loads(
                sign, salt='email-verify', max_age=86400)
            if data.get('user_id') != user.id:
                raise django_signing.BadSignature
        except django_signing.BadSignature:
            return Response({'error': '链接无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=['is_active', 'last_modify_time'])
        return Response({'success': True, 'message': '邮箱验证成功，账号已激活'})


class LogoutAPIView(APIView):
    """用户登出"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        delete_sidebar_cache()
        response = Response({'success': True})
        response.delete_cookie('logged_user')
        return response


class UserInfoAPIView(APIView):
    """当前登录用户信息"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(BlogUserSerializer(request.user).data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if 'nickname' in serializer.validated_data:
            request.user.nickname = serializer.validated_data['nickname']
            request.user.save(update_fields=['nickname', 'last_modify_time'])
        return Response(BlogUserSerializer(request.user).data)


class AvatarUploadAPIView(APIView):
    """上传用户头像（multipart/form-data）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('avatar')
        if not file:
            return Response({'error': '未选择头像文件'}, status=status.HTTP_400_BAD_REQUEST)
        MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
        if file.size > MAX_AVATAR_SIZE:
            return Response({'error': '头像文件过大，最大允许 2MB'}, status=status.HTTP_400_BAD_REQUEST)
        img = Image.open(file)
        img.verify()
        ext = os.path.splitext(file.name)[1].lower() or '.jpg'
        if ext not in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            return Response({'error': '不支持的图片格式'}, status=status.HTTP_400_BAD_REQUEST)
        filename = uuid.uuid4().hex + ext
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatar')
        os.makedirs(avatar_dir, exist_ok=True)
        savepath = os.path.join(avatar_dir, filename)
        file.seek(0)
        # 重新用 Pillow 转码保存，剥离可能嵌入图片的恶意内容（防伪装文件）
        try:
            img = Image.open(file)
            img.save(savepath, quality=85, optimize=True)
        except Exception:
            return Response({'error': '无效的图片文件'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.avatar = settings.MEDIA_URL + 'avatar/' + filename
        request.user.save(update_fields=['avatar', 'last_modify_time'])
        return Response({'success': True, 'avatar': request.user.avatar})


class EmailThrottle(throttling.SimpleRateThrottle):
    """邮件发送节流：每个 IP 每小时最多 3 次"""
    scope = 'email'
    rate = '3/hour'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PasswordResetThrottle(throttling.SimpleRateThrottle):
    """密码重置尝试节流：每个 IP 每小时最多 10 次，防验证码暴力破解"""
    scope = 'password_reset'
    rate = '10/hour'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class ChangeEmailAPIView(APIView):
    """修改邮箱：发送验证邮件到新邮箱，点击链接后生效"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        serializer = ChangeEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data['new_email']
        sign = django_signing.dumps(
            {'user_id': request.user.id, 'new_email': new_email},
            salt='change-email',
        )
        site = get_current_site().domain
        if settings.DEBUG:
            site = '127.0.0.1:8000'
        path = reverse('accounts:change_email_confirm', kwargs={
            'id': request.user.id, 'sign': sign})
        url = "http://{site}{path}?email={email}".format(
            site=site, path=path, email=new_email)
        content = """
        <p>请点击下面链接确认修改您的邮箱为：{email}</p>
        <a href="{url}" rel="bookmark">{url}</a>
        <br />
        如果上面链接无法打开，请将此链接复制至浏览器：{url}
        """.format(email=new_email, url=url)
        send_email(emailto=[new_email], title='确认修改邮箱', content=content)
        return Response({'success': True, 'message': '验证邮件已发送至新邮箱，请查收后点击链接确认'})


class ForgetPasswordAPIView(APIView):
    """忘记密码：验证邮箱验证码后重置密码"""
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # 验证邮箱验证码
        error = verify(email, code)
        if error:
            return Response({'error': str(error)}, status=status.HTTP_400_BAD_REQUEST)

        user = BlogUser.objects.filter(email=email).first()
        if not user:
            return Response({'error': '该邮箱未注册'}, status=status.HTTP_404_NOT_FOUND)
        user.password = make_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password', 'last_modify_time'])
        return Response({'success': True, 'message': '密码重置成功'})


class ForgetPasswordEmailCodeAPIView(APIView):
    """发送忘记密码的验证码邮件"""
    permission_classes = [AllowAny]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        serializer = VerifyEmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = generate_code()
        send_verify_email(email, code)
        set_code(email, code)
        return Response({'success': True, 'message': '验证码已发送'})


class ChangePasswordAPIView(APIView):
    """修改密码（需登录）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': '原密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'success': True, 'message': '密码修改成功'})
