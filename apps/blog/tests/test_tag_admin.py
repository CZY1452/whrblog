"""
Blog Tag Admin 测试
测试标签后台管理功能
"""
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from apps.blog.models import Tag
from core.tests.test_base import BaseTestCase, AdminTestMixin


class TagAdminTest(BaseTestCase, AdminTestMixin):
    """测试 Tag Admin"""

    def test_tag_admin_list(self):
        """测试标签列表"""
        self.login_admin()
        response = self.assert_admin_accessible(Tag)
        self.assertContains(response, self.tag.name)

    def test_tag_admin_search(self):
        """测试标签搜索"""
        self.login_admin()
        url = self.get_admin_url(Tag)
        response = self.client.get(url, {'q': self.tag.name})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tag.name)

    def test_tag_admin_change(self):
        """测试修改标签"""
        self.login_admin()
        url = self.get_admin_change_url(self.tag)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
