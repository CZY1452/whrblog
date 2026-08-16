"""
Blog Category Admin 测试
测试分类后台管理功能
"""
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from apps.blog.models import Category
from core.tests.test_base import BaseTestCase, AdminTestMixin


class CategoryAdminTest(BaseTestCase, AdminTestMixin):
    """测试 Category Admin"""

    def test_category_admin_list(self):
        """测试分类列表"""
        self.login_admin()
        response = self.assert_admin_accessible(Category)
        self.assertContains(response, self.category.name)

    def test_category_admin_search(self):
        """测试分类搜索"""
        self.login_admin()
        url = self.get_admin_url(Category)
        response = self.client.get(url, {'q': self.category.name})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    def test_category_admin_change(self):
        """测试修改分类"""
        self.login_admin()
        url = self.get_admin_change_url(self.category)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
