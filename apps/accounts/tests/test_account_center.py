"""
用户中心 API 测试
覆盖：个人资料 / 修改昵称 / 修改密码 / 修改邮箱 / 头像上传
"""
import io
import json

from PIL import Image

from core.tests.test_base import BaseTestCase


class ProfileApiTest(BaseTestCase):
    """个人资料展示与修改"""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_get_profile(self):
        response = self.client.get('/api/user')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['username'], self.user.username)
        self.assertIn('avatar', data)
        self.assertIn('nickname', data)

    def test_patch_nickname(self):
        response = self.client.patch('/api/user', data=json.dumps({'nickname': '新昵称'}),
                                     content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['nickname'], '新昵称')
        self.user.refresh_from_db()
        self.assertEqual(self.user.nickname, '新昵称')

    def test_user_info_requires_auth(self):
        anon = self.client.__class__()
        response = anon.get('/api/user')
        self.assertEqual(response.status_code, 403)


class PasswordApiTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_change_password_success(self):
        response = self.client.post('/api/change_password', data=json.dumps({
            'old_password': 'testpass123', 'new_password': 'newpass123',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_password_wrong_old(self):
        response = self.client.post('/api/change_password', data=json.dumps({
            'old_password': 'wrong', 'new_password': 'newpass123',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)


class EmailApiTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_change_email_sends_verification(self):
        response = self.client.post('/api/change_email', data=json.dumps({
            'new_email': 'brandnew@test.com',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'test@test.com')

    def test_change_email_duplicate(self):
        self.create_user('other_user', email='other@test.com')
        response = self.client.post('/api/change_email', data=json.dumps({
            'new_email': 'other@test.com',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)


class AvatarApiTest(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_upload_avatar(self):
        buf = io.BytesIO()
        Image.new('RGB', (8, 8), (0, 128, 0)).save(buf, format='PNG')
        buf.seek(0)
        response = self.client.post('/api/upload_avatar',
                                    {'avatar': buf}, format='multipart')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['avatar'].startswith('/media/avatar/'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.avatar, data['avatar'])

    def test_upload_avatar_missing_file(self):
        response = self.client.post('/api/upload_avatar', {}, format='multipart')
        self.assertEqual(response.status_code, 400)


