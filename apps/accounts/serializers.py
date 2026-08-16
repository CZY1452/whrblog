from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from apps.accounts.models import BlogUser
from apps.accounts.utils import get_code, verify


class BlogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogUser
        fields = ['id', 'username', 'nickname', 'avatar', 'email', 'is_superuser', 'date_joined']
        read_only_fields = ['id', 'is_superuser', 'date_joined']


class UpdateProfileSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_nickname(self, value):
        return value.strip()


class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField()

    def validate_new_email(self, value):
        from apps.accounts.models import BlogUser
        if BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱已被使用')
        return value


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = BlogUser
        fields = ['username', 'email', 'nickname', 'password', 'password_confirm']

    def validate_username(self, value):
        if BlogUser.objects.filter(username=value).exists():
            raise serializers.ValidationError('用户名已存在')
        return value

    def validate_email(self, value):
        if BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('邮箱已被注册')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs

    def create(self, validated_data):
        import hashlib
        validated_data.pop('password_confirm')
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['is_active'] = False
        validated_data['source'] = 'Register'
        email = validated_data.get('email') or ''
        hash_ = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
        validated_data['avatar'] = 'https://www.gravatar.com/avatar/{hash}?s=80&d=mp'.format(hash=hash_)
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
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs


class VerifyEmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not BlogUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('该邮箱未注册')
        return value


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
