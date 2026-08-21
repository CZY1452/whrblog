"""
用户注册业务逻辑测试用例
包括用户注册、创建、默认状态等核心业务逻辑
"""
from django.test import TestCase

from apps.accounts.models import BlogUser


class UserRegistrationTest(TestCase):
    """测试用户注册业务逻辑"""

    def test_user_can_be_created(self):
        """测试用户可以被创建"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')

    def test_user_password_is_hashed(self):
        """测试用户密码被哈希存储"""
        password = 'testpassword123'
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=password
        )

        # 密码不应该以明文存储
        self.assertNotEqual(user.password, password)
        # 密码应该被哈希
        self.assertTrue(user.password.startswith('pbkdf2_'))

    def test_user_can_check_password(self):
        """测试用户可以验证密码"""
        password = 'testpassword123'
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password=password
        )

        # 正确的密码应该通过验证
        self.assertTrue(user.check_password(password))
        # 错误的密码应该不通过验证
        self.assertFalse(user.check_password('wrongpassword'))

    def test_username_must_be_unique(self):
        """测试用户名必须唯一"""
        BlogUser.objects.create_user(
            username='testuser',
            email='test1@example.com',
            password='password'
        )

        # 尝试创建相同用户名的用户应该失败
        with self.assertRaises(Exception):
            BlogUser.objects.create_user(
                username='testuser',
                email='test2@example.com',
                password='password'
            )

    def test_email_is_stored_correctly(self):
        """测试邮箱正确存储"""
        email = 'test@example.com'
        user = BlogUser.objects.create_user(
            username='testuser',
            email=email,
            password='password'
        )

        self.assertEqual(user.email, email)

    def test_user_is_active_by_default(self):
        """测试用户默认是激活状态"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        self.assertTrue(user.is_active)

    def test_user_is_not_staff_by_default(self):
        """测试用户默认不是staff"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        self.assertFalse(user.is_staff)

    def test_user_is_not_superuser_by_default(self):
        """测试用户默认不是超级用户"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        self.assertFalse(user.is_superuser)
