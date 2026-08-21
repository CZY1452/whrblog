from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from apps.accounts.models import BlogUser

# 默认头像：本地静态图，所有未自定义头像的用户共用
DEFAULT_AVATAR_URL = settings.MEDIA_URL + 'avatar/1.png'


class BlogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogUser
        fields = ['id', 'username', 'nickname', 'avatar', 'email', 'is_superuser', 'date_joined']
        read_only_fields = ['id', 'is_superuser', 'date_joined']


class UpdateProfileSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_nickname(self, value):
        """昵称去除首尾空白"""
        return value.strip()


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        """校验新邮箱未被其他用户占用"""
        from apps.accounts.models import BlogUser
        if BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被使用')
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)
    code = serializers.CharField(write_only=True)

    class Meta:
        model = BlogUser
        fields = ['username', 'email', 'nickname', 'password', 'password_confirm', 'code']

    def validate_username(self, value):
        """校验用户名唯一"""
        if BlogUser.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate_email(self, value):
        """校验邮箱唯一"""
        if BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('邮箱已被注册')
        return value

    def validate(self, attrs):
        """校验两次输入的密码一致"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs

    def create(self, validated_data):
        """创建用户：密码加密、验证码仅校验不入库、写入默认头像与注册来源"""
        validated_data.pop('password_confirm')
        validated_data.pop('code', None)  # 验证码仅用于校验，不入库
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = False
        validated_data['source'] = 'Register'
        # 默认头像改为本地图（不再用 Gravatar 外链）
        validated_data['avatar'] = DEFAULT_AVATAR_URL
        return BlogUser.objects.create(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    remember = serializers.BooleanField(required=False, default=False)


class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """校验两次输入的新密码一致"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs


class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """校验邮箱已注册（找回密码发码前置检查）"""
        if not BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱未注册')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
