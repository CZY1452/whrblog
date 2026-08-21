"""
账号页公开 API 测试
覆盖前端化账号页对应的数据端点：登录 / 注册 / 忘记密码
"""
import json

from django.urls import reverse

from core.tests.test_base import BaseTestCase


class LoginApiTest(BaseTestCase):
    """登录 API"""

    def test_login_success(self):
        user = self.user
        url = reverse('accounts:api-login')
        response = self.client.post(url, data=json.dumps({
            'username': user.username,
            'password': 'testpass123',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['username'], user.username)
        self.assertIn('logged_user', response.cookies)

    def test_login_wrong_credentials(self):
        url = reverse('accounts:api-login')
        response = self.client.post(url, data=json.dumps({
            'username': 'nobody',
            'password': 'wrong',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_login_inactive_user(self):
        user = self.create_user('inactive_user')
        user.is_active = False
        user.save()
        url = reverse('accounts:api-login')
        response = self.client.post(url, data=json.dumps({
            'username': user.username,
            'password': 'testpass123',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)


class RegisterApiTest(BaseTestCase):
    """注册 API"""

    def test_register_with_code_activates_user(self):
        """新注册流程：先发验证码，携带 code 注册，校验通过即激活"""
        from apps.accounts.utils import set_reg_code
        email = 'newbie@test.com'
        set_reg_code(email, '123456')  # 模拟邮箱已收到验证码（写入缓存）
        url = reverse('accounts:api-register')
        response = self.client.post(url, data=json.dumps({
            'username': 'newbie',
            'email': email,
            'nickname': '新用户',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'code': '123456',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        # is_active 不在序列化器字段中，通过数据库验证（验证码通过即激活）
        from apps.accounts.models import BlogUser
        new_user = BlogUser.objects.get(username='newbie')
        self.assertTrue(new_user.is_active)

    def test_register_wrong_code_rejected(self):
        """注册时验证码错误应返回 400 且不创建用户"""
        from apps.accounts.utils import set_reg_code
        email = 'wrongcode@test.com'
        set_reg_code(email, '123456')
        url = reverse('accounts:api-register')
        response = self.client.post(url, data=json.dumps({
            'username': 'wrongcode',
            'email': email,
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'code': '000000',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        from apps.accounts.models import BlogUser
        self.assertFalse(BlogUser.objects.filter(username='wrongcode').exists())

    def test_register_password_mismatch(self):
        url = reverse('accounts:api-register')
        response = self.client.post(url, data=json.dumps({
            'username': 'mismatch',
            'email': 'mismatch@test.com',
            'password': 'testpass123',
            'password_confirm': 'different',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)


class ForgetPasswordApiTest(BaseTestCase):
    """忘记密码 API"""

    def test_send_code_valid_email(self):
        url = reverse('accounts:api-forget-password-code')
        response = self.client.post(url, data=json.dumps({
            'email': 'test@test.com',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_send_code_unknown_email(self):
        url = reverse('accounts:api-forget-password-code')
        response = self.client.post(url, data=json.dumps({
            'email': 'unknown@test.com',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_reset_password_mismatch(self):
        url = reverse('accounts:api-forget-password')
        response = self.client.post(url, data=json.dumps({
            'email': 'test@test.com',
            'new_password': 'newpass123',
            'new_password_confirm': 'different',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_reset_password_unknown_email(self):
        url = reverse('accounts:api-forget-password')
        response = self.client.post(url, data=json.dumps({
            'email': 'unknown@test.com',
            'code': '000000',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123',
        }), content_type='application/json')
        # 验证码校验先于邮箱存在性检查，未存储验证码时返回 400
        self.assertIn(response.status_code, [400, 404])
