"""
Test cases for user permissions and activation business logic
包括用户权限管理、激活/停用等核心业务逻辑
"""
from django.test import TestCase

from apps.accounts.models import BlogUser


class UserPermissionTest(TestCase):
    """测试用户权限业务逻辑"""

    def setUp(self):
        """设置测试环境"""
        self.normal_user = BlogUser.objects.create_user(
            username='normaluser',
            email='normal@example.com',
            password='password'
        )

        self.staff_user = BlogUser.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='password',
            is_staff=True
        )

        self.superuser = BlogUser.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='password'
        )

    def test_normal_user_has_no_special_privileges(self):
        """测试普通用户没有特殊权限"""
        self.assertFalse(self.normal_user.is_staff)
        self.assertFalse(self.normal_user.is_superuser)

    def test_staff_user_is_staff(self):
        """测试staff用户有staff权限"""
        self.assertTrue(self.staff_user.is_staff)
        # staff用户不一定是超级用户
        self.assertFalse(self.staff_user.is_superuser)

    def test_superuser_has_all_privileges(self):
        """测试超级用户有所有权限"""
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.is_active)

    def test_create_superuser_method(self):
        """测试创建超级用户的方法"""
        superuser = BlogUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )

        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_can_be_promoted_to_staff(self):
        """测试用户可以提升为staff"""
        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )

        self.assertFalse(user.is_staff)

        # 提升为staff
        user.is_staff = True
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.is_staff)

    def test_user_can_be_promoted_to_superuser(self):
        """测试用户可以提升为超级用户"""
        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )

        self.assertFalse(user.is_superuser)

        # 提升为超级用户
        user.is_superuser = True
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.is_superuser)


class UserActivationTest(TestCase):
    """测试用户激活业务逻辑"""

    def test_user_can_be_deactivated(self):
        """测试用户可以被停用"""
        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )

        self.assertTrue(user.is_active)

        # 停用用户
        user.is_active = False
        user.save()

        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_user_can_be_reactivated(self):
        """测试用户可以被重新激活"""
        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password',
            is_active=False
        )

        self.assertFalse(user.is_active)

        # 重新激活用户
        user.is_active = True
        user.save()

        user.refresh_from_db()
        self.assertTrue(user.is_active)
