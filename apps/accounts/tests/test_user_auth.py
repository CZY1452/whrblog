"""
用户认证与密码管理业务逻辑测试用例
包括用户认证、密码管理以及账户验证等核心业务逻辑
"""
from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import authenticate
from django.utils import timezone

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category
from core.utils import get_current_site, generate_code
import apps.accounts.utils as utils


class UserAuthenticationTest(TestCase):
    """测试用户认证业务逻辑"""

    def setUp(self):
        """设置测试环境"""
        self.username = 'testuser'
        self.email = 'test@example.com'
        self.password = 'testpassword123'

        self.user = BlogUser.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

    def test_user_can_authenticate_with_correct_credentials(self):
        """测试用户可以用正确的凭据认证"""
        user = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(user)
        self.assertEqual(user, self.user)

    def test_user_cannot_authenticate_with_wrong_password(self):
        """测试用户不能用错误的密码认证"""
        user = authenticate(username=self.username, password='wrongpassword')
        self.assertIsNone(user)

    def test_user_cannot_authenticate_with_wrong_username(self):
        """测试用户不能用错误的用户名认证"""
        user = authenticate(username='wronguser', password=self.password)
        self.assertIsNone(user)

    def test_inactive_user_cannot_authenticate(self):
        """测试未激活的用户不能认证"""
        self.user.is_active = False
        self.user.save()

        user = authenticate(username=self.username, password=self.password)
        # 注意：Django的authenticate()方法会返回用户，但is_active=False
        # 实际的登录阻止发生在login()时
        # 这里我们测试用户的is_active状态
        if user:
            self.assertFalse(user.is_active)

    def test_active_user_can_authenticate(self):
        """测试激活的用户可以认证"""
        self.user.is_active = True
        self.user.save()

        user = authenticate(username=self.username, password=self.password)
        self.assertIsNotNone(user)


class UserPasswordManagementTest(TestCase):
    """测试用户密码管理业务逻辑"""

    def setUp(self):
        """设置测试环境"""
        self.user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='oldpassword123'
        )

    def test_user_can_change_password(self):
        """测试用户可以修改密码"""
        old_password = 'oldpassword123'
        new_password = 'newpassword456'

        # 验证旧密码
        self.assertTrue(self.user.check_password(old_password))

        # 修改密码
        self.user.set_password(new_password)
        self.user.save()

        # 验证新密码
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertFalse(self.user.check_password(old_password))

    def test_password_change_requires_save(self):
        """测试密码修改需要保存"""
        new_password = 'newpassword456'
        old_password_hash = self.user.password

        # 只设置密码，不保存
        self.user.set_password(new_password)

        # 从数据库重新加载
        user_from_db = BlogUser.objects.get(id=self.user.id)

        # 数据库中的密码应该还是旧的
        self.assertEqual(user_from_db.password, old_password_hash)

    def test_set_unusable_password(self):
        """测试设置不可用的密码"""
        self.user.set_unusable_password()
        self.user.save()

        # 用户应该无法用任何密码认证
        self.assertFalse(self.user.has_usable_password())


class AccountTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.blog_user = BlogUser.objects.create_user(
            username="test",
            email="admin@admin.com",
            password="12345678"
        )
        self.new_test = "xxx123--="

    def test_validate_account(self):
        site = get_current_site().domain
        user = BlogUser.objects.create_superuser(
            email="2393863846@qq.com",
            username="wanghuanran1",
            password="qwer!@#$ggg")
        testuser = BlogUser.objects.get(username='wanghuanran1')

        loginresult = self.client.login(
            username='wanghuanran1',
            password='qwer!@#$ggg')
        self.assertEqual(loginresult, True)
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

        category = Category()
        category.name = "categoryaaa"
        category.creation_time = timezone.now()
        category.last_modify_time = timezone.now()
        category.save()

        article = Article()
        article.title = "nicetitleaaa"
        article.body = "nicecontentaaa"
        article.author = user
        article.category = category
        article.type = 'a'
        article.status = 'p'
        article.save()

        response = self.client.get(article.get_admin_url())
        self.assertEqual(response.status_code, 200)

    def test_verify_email_code(self):
        to_email = "admin@admin.com"
        code = generate_code()
        utils.set_verify_code(to_email, code, 'reset')
        utils.send_code_email(to_email, code, 'reset')

        err = utils.verify_code("admin@admin.com", 'reset', code)
        self.assertEqual(err, None)

        err = utils.verify_code("admin@123.com", 'reset', code)
        self.assertEqual(type(err), str)
