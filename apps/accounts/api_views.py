import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
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
from apps.accounts.utils import (
    send_code_email,
    set_verify_code,
    verify_code,
    code_can_send,
    code_mark_sent,
)
from core.utils import (
    delete_sidebar_cache,
    generate_code,
)

logger = logging.getLogger(__name__)


class RegisterAPIView(APIView):
    """用户注册（注册页内联邮箱验证码验证，验证通过即激活）"""
    permission_classes = [AllowAny]

    def post(self, request):
        """注册：校验邮箱验证码后创建并激活用户（验证码正确即 is_active=True）"""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = (serializer.validated_data.get('code') or '').strip()

        # 校验邮箱验证码（6 位，1 分钟有效），成功即删除防复用
        error = verify_code(email, 'register', code)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()  # create 中默认 is_active=False
        user.is_active = True     # 验证码已校验，直接激活
        user.save(update_fields=['is_active', 'last_modify_time'])

        return Response({
            'success': True,
            'message': '注册成功，邮箱已验证，请登录',
        }, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    """用户登录"""
    permission_classes = [AllowAny]

    def post(self, request):
        """登录：校验用户名密码并建立会话；remember 为 True 时延长会话有效期"""
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
    """邮箱激活验证（注册验证码方式，SPA /verify-email 调用此接口）"""
    permission_classes = [AllowAny]

    def post(self, request):
        """邮箱激活：按用户 id + 验证码激活未激活账号（SPA /verify-email 调用）"""
        user_id = request.data.get('id')
        code = request.data.get('code')
        if not user_id or not code:
            return Response({'error': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        user = BlogUser.objects.filter(pk=user_id).first()
        if not user:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
        if user.is_active:
            return Response({'success': True, 'message': '账号已激活'})
        error = verify_code(user.email, 'register', code)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save(update_fields=['is_active', 'last_modify_time'])
        return Response({'success': True, 'message': '邮箱验证成功，账号已激活'})


class LogoutAPIView(APIView):
    """用户登出"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """登出：销毁当前会话并清除 logged_user Cookie"""
        logout(request)
        delete_sidebar_cache()
        response = Response({'success': True})
        response.delete_cookie('logged_user')
        return response


class UserInfoAPIView(APIView):
    """当前登录用户信息"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取当前登录用户信息"""
        return Response(BlogUserSerializer(request.user).data)

    def patch(self, request):
        """更新当前用户昵称（仅 nickname 字段）"""
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
        """上传头像：2MB 限制、格式白名单、Pillow 重新转码后保存并更新用户头像"""
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
        """按 IP 生成邮箱类限流缓存键（重发注册码/忘记密码发码共用）"""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PasswordResetThrottle(throttling.SimpleRateThrottle):
    """密码重置尝试节流：每个 IP 每小时最多 10 次，防验证码暴力破解"""
    scope = 'password_reset'
    rate = '10/hour'

    def get_cache_key(self, request, view):
        """按 IP 生成密码重置限流缓存键（防验证码暴力破解）"""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class RegisterCodeThrottle(throttling.SimpleRateThrottle):
    """注册验证码发送节流：每个 IP 每小时最多 20 次（另有「每邮箱 1 分钟冷却」兜底防刷）"""
    scope = 'register_code'
    rate = '20/hour'

    def get_cache_key(self, request, view):
        """按 IP 生成注册验证码限流缓存键"""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class SendRegisterCodeAPIView(APIView):
    """注册页「发送验证码」：向注册邮箱发送 6 位验证码（1 分钟有效 + 1 分钟冷却 + IP 限流）"""
    permission_classes = [AllowAny]
    throttle_classes = [RegisterCodeThrottle]

    def post(self, request):
        """发送注册验证码：校验邮箱格式与未注册、1 分钟冷却与 IP 限流后发码"""
        email = (request.data.get('email') or '').strip()
        if not email or '@' not in email or '.' not in email.split('@')[-1]:
            return Response({'error': '请填写正确的邮箱'}, status=status.HTTP_400_BAD_REQUEST)
        if BlogUser.objects.filter(email=email).exists():
            return Response({'error': '该邮箱已注册'}, status=status.HTTP_400_BAD_REQUEST)
        if not code_can_send(email, 'register'):
            return Response(
                {'error': '验证码发送过于频繁，请 1 分钟后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        code = generate_code()
        set_verify_code(email, code, 'register')
        code_mark_sent(email, 'register')
        send_code_email(email, code, 'register')
        return Response({'success': True, 'message': '验证码已发送，请查收邮箱（1 分钟内有效）'})


class ResendVerifyEmailAPIView(APIView):
    """重新发送注册验证码（1 分钟冷却 + IP 限流）"""
    permission_classes = [AllowAny]
    throttle_classes = [EmailThrottle]

    def post(self, request):
        """重新发送注册验证码：给未激活账号重新发码（1 分钟冷却 + IP 限流）"""
        user_id = request.data.get('id')
        if not user_id:
            return Response({'error': '参数缺失'}, status=status.HTTP_400_BAD_REQUEST)
        user = BlogUser.objects.filter(pk=user_id, is_active=False).first()
        if not user:
            return Response({'error': '用户不存在或已激活'}, status=status.HTTP_404_NOT_FOUND)
        if not code_can_send(user.email, 'register'):
            return Response(
                {'error': '验证码发送过于频繁，请 1 分钟后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        code = generate_code()
        set_verify_code(user.email, code, 'register')
        code_mark_sent(user.email, 'register')
        send_code_email(user.email, code, 'register')
        return Response({'success': True, 'message': '验证码已重新发送'})


class ChangeEmailCodeThrottle(throttling.SimpleRateThrottle):
    """修改邮箱验证码发送节流：每 IP 每小时最多 20 次（另有每邮箱 1 分钟冷却兜底）"""
    scope = 'change_email_code'
    rate = '20/hour'

    def get_cache_key(self, request, view):
        """按 IP 生成改邮箱验证码限流缓存键"""
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class SendChangeEmailCodeAPIView(APIView):
    """修改邮箱「发送验证码」：向新邮箱发送 6 位验证码（1 分钟有效 + 1 分钟冷却 + IP 限流）"""
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChangeEmailCodeThrottle]

    def post(self, request):
        """发送改邮箱验证码：校验新邮箱未占用、1 分钟冷却与 IP 限流后发码"""
        new_email = (request.data.get('new_email') or '').strip()
        if not new_email or '@' not in new_email or '.' not in new_email.split('@')[-1]:
            return Response({'error': '请填写正确的邮箱'}, status=status.HTTP_400_BAD_REQUEST)
        if BlogUser.objects.filter(email=new_email).exists():
            return Response({'error': '该邮箱已被使用'}, status=status.HTTP_400_BAD_REQUEST)
        if not code_can_send(new_email, 'change_email'):
            return Response(
                {'error': '验证码发送过于频繁，请 1 分钟后再试'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        code = generate_code()
        set_verify_code(new_email, code, 'change_email')
        code_mark_sent(new_email, 'change_email')
        send_code_email(new_email, code, 'change_email')
        return Response({'success': True, 'message': '验证码已发送至新邮箱，请查收（1 分钟内有效）'})


class ChangeEmailAPIView(APIView):
    """修改邮箱：校验新邮箱验证码后更新邮箱"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """修改邮箱：校验新邮箱验证码正确后更新用户邮箱（验证码即删防复用）"""
        serializer = ChangeEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data['new_email']
        code = (request.data.get('code') or '').strip()
        if not code:
            return Response({'error': '请输入邮箱验证码'}, status=status.HTTP_400_BAD_REQUEST)

        # 校验新邮箱收到的验证码（1 分钟有效，成功即删除防复用）
        error = verify_code(new_email, 'change_email', code)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        request.user.email = new_email
        request.user.save(update_fields=['email', 'last_modify_time'])
        return Response({'success': True, 'message': '邮箱修改成功'})


class ForgetPasswordAPIView(APIView):
    """忘记密码：验证邮箱验证码后重置密码"""
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        """忘记密码：校验邮箱验证码后重置密码（限流 10/hour）"""
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # 验证邮箱验证码
        error = verify_code(email, 'reset', code)
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
        """发送密码重置验证码到注册邮箱"""
        serializer = VerifyEmailCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = generate_code()
        set_verify_code(email, code, 'reset')
        send_code_email(email, code, 'reset')
        return Response({'success': True, 'message': '验证码已发送'})


class ChangePasswordAPIView(APIView):
    """修改密码（需登录）"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """修改密码：校验原密码正确后设置新密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': '原密码错误'}, status=status.HTTP_400_BAD_REQUEST)
        user.password = make_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'success': True, 'message': '密码修改成功'})
