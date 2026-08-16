"""
文章创建 API 测试
覆盖：管理员发布文章 / 普通用户与匿名用户无权限
"""
import json

from core.tests.test_base import BaseTestCase


class ArticleCreateApiTest(BaseTestCase):
    """发表文章 API"""

    def test_admin_can_create_published_article(self):
        self.login_admin()
        response = self.client.post('/api/article_create', data=json.dumps({
            'title': '新文章',
            'body': '# 标题\n正文内容',
            'category': self.category.id,
            'tags': [self.tag.id],
            'status': 'p',
            'comment_status': 'o',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['title'], '新文章')
        self.assertEqual(data['status'], 'p')
        self.assertIn('正文内容', data['body'])

    def test_admin_can_save_draft(self):
        self.login_admin()
        response = self.client.post('/api/article_create', data=json.dumps({
            'title': '草稿文章',
            'body': '草稿内容',
            'category': self.category.id,
            'status': 'd',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['status'], 'd')

    def test_normal_user_forbidden(self):
        self.login_user()
        response = self.client.post('/api/article_create', data=json.dumps({
            'title': '匿名文章',
            'body': '内容',
            'category': self.category.id,
        }), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_forbidden(self):
        response = self.client.post('/api/article_create', data=json.dumps({
            'title': '匿名文章',
            'body': '内容',
            'category': self.category.id,
        }), content_type='application/json')
        self.assertEqual(response.status_code, 403)

    def test_missing_title_returns_400(self):
        self.login_admin()
        response = self.client.post('/api/article_create', data=json.dumps({
            'body': '没有标题',
            'category': self.category.id,
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_missing_category_returns_400(self):
        self.login_admin()
        response = self.client.post('/api/article_create', data=json.dumps({
            'title': '没有分类',
            'body': '内容',
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
