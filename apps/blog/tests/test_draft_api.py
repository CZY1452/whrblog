"""
草稿箱 API 测试
覆盖：草稿列表、详情、编辑、删除、发布，以及权限控制
"""
import json

from core.tests.test_base import BaseTestCase


class DraftListApiTest(BaseTestCase):
    """草稿箱列表 API"""

    def test_admin_can_list_drafts(self):
        """管理员可以获取草稿列表"""
        self.login_admin()
        # 创建草稿
        self.create_article(title='草稿1', status='d')
        self.create_article(title='草稿2', status='d')
        self.create_article(title='已发布', status='p')

        response = self.client.get('/api/drafts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 只返回草稿，不返回已发布文章
        self.assertEqual(len(data['results']), 2)

    def test_drafts_ordered_by_modify_time(self):
        """草稿按修改时间倒序排列"""
        self.login_admin()
        self.create_article(title='旧草稿', status='d')
        self.create_article(title='新草稿', status='d')

        response = self.client.get('/api/drafts/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results[0]['title'], '新草稿')

    def test_normal_user_cannot_list_drafts(self):
        """普通用户无法访问草稿列表"""
        self.login_user()
        response = self.client.get('/api/drafts/')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_list_drafts(self):
        """匿名用户无法访问草稿列表"""
        response = self.client.get('/api/drafts/')
        self.assertEqual(response.status_code, 403)


class DraftDetailApiTest(BaseTestCase):
    """草稿详情 API"""

    def test_admin_can_retrieve_draft(self):
        """管理员可以获取草稿详情"""
        self.login_admin()
        draft = self.create_article(title='草稿详情', body='# 内容', status='d')

        response = self.client.get(f'/api/drafts/{draft.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], '草稿详情')
        # retrieve 使用 ArticleCreateSerializer，返回原始 body
        self.assertIn('# 内容', data['body'])

    def test_normal_user_cannot_retrieve_draft(self):
        """普通用户无法查看草稿详情"""
        self.login_user()
        draft = self.create_article(title='草稿', status='d')
        response = self.client.get(f'/api/drafts/{draft.id}/')
        self.assertEqual(response.status_code, 403)


class DraftUpdateApiTest(BaseTestCase):
    """草稿编辑 API"""

    def test_admin_can_edit_draft(self):
        """管理员可以编辑草稿"""
        self.login_admin()
        draft = self.create_article(title='旧标题', body='旧内容', status='d')

        response = self.client.patch(
            f'/api/drafts/{draft.id}/',
            data=json.dumps({'title': '新标题'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], '新标题')

    def test_normal_user_cannot_edit_draft(self):
        """普通用户无法编辑草稿"""
        self.login_user()
        draft = self.create_article(title='草稿', status='d')
        response = self.client.patch(
            f'/api/drafts/{draft.id}/',
            data=json.dumps({'title': '修改'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)


class DraftDeleteApiTest(BaseTestCase):
    """草稿删除 API"""

    def test_admin_can_delete_draft(self):
        """管理员可以删除草稿"""
        self.login_admin()
        draft = self.create_article(title='要删除的草稿', status='d')
        draft_id = draft.id

        response = self.client.delete(f'/api/drafts/{draft_id}/')
        self.assertEqual(response.status_code, 204)

        # 验证已删除
        from apps.blog.models import Article
        self.assertFalse(Article.objects.filter(id=draft_id).exists())

    def test_normal_user_cannot_delete_draft(self):
        """普通用户无法删除草稿"""
        self.login_user()
        draft = self.create_article(title='草稿', status='d')
        response = self.client.delete(f'/api/drafts/{draft.id}/')
        self.assertEqual(response.status_code, 403)


class DraftPublishApiTest(BaseTestCase):
    """草稿发布 API"""

    def test_admin_can_publish_draft(self):
        """管理员可以发布草稿"""
        self.login_admin()
        draft = self.create_article(title='待发布', body='内容', status='d')

        response = self.client.post(f'/api/drafts/{draft.id}/publish/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'p')

    def test_published_draft_no_longer_in_draft_list(self):
        """发布后的草稿不再出现在草稿列表中"""
        self.login_admin()
        draft = self.create_article(title='即将发布', status='d')

        # 发布
        self.client.post(f'/api/drafts/{draft.id}/publish/')

        # 检查草稿列表
        response = self.client.get('/api/drafts/')
        results = response.json()['results']
        titles = [r['title'] for r in results]
        self.assertNotIn('即将发布', titles)

    def test_normal_user_cannot_publish_draft(self):
        """普通用户无法发布草稿"""
        self.login_user()
        draft = self.create_article(title='草稿', status='d')
        response = self.client.post(f'/api/drafts/{draft.id}/publish/')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_publish_draft(self):
        """匿名用户无法发布草稿"""
        draft = self.create_article(title='草稿', status='d')
        response = self.client.post(f'/api/drafts/{draft.id}/publish/')
        self.assertEqual(response.status_code, 403)
