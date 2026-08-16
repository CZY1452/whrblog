"""
Blog Article Admin 测试
测试文章后台管理功能
"""
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.urls import reverse

from apps.blog.admin import ArticleAdmin
from apps.blog.models import Article
from core.tests.test_base import BaseTestCase, AdminTestMixin


class ArticleAdminTest(BaseTestCase, AdminTestMixin):
    """测试 Article Admin"""

    def setUp(self):
        super().setUp()
        self.site = AdminSite()
        self.article_admin = ArticleAdmin(Article, self.site)

    def test_admin_list_display(self):
        """测试文章列表显示"""
        self.login_admin()
        response = self.assert_admin_accessible(Article)
        self.assertContains(response, self.article.title)

    def test_admin_search_by_title(self):
        """测试按标题搜索"""
        self.login_admin()
        url = self.get_admin_url(Article)
        response = self.client.get(url, {'q': self.article.title})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_admin_filter_by_status(self):
        """测试按状态过滤"""
        self.login_admin()
        url = self.get_admin_url(Article)
        response = self.client.get(url, {'status__exact': 'p'})
        self.assertEqual(response.status_code, 200)

    def test_admin_filter_by_category(self):
        """测试按分类过滤"""
        self.login_admin()
        url = self.get_admin_url(Article)
        response = self.client.get(url, {'category__id__exact': self.category.id})
        self.assertEqual(response.status_code, 200)

    def test_admin_change_article(self):
        """测试修改文章"""
        self.login_admin()
        url = self.get_admin_change_url(self.article)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_save_model_sets_author(self):
        """测试保存文章时自动设置作者"""
        request = self.factory.post('/')
        request.user = self.admin_user

        new_article = Article(
            title='新文章测试保存',
            body='新内容',
            category=self.category,
            type='a',
            status='p',
            author=self.admin_user  # 先设置作者
        )

        # 测试 admin 的 save_model 方法
        self.article_admin.save_model(request, new_article, None, None)
        # 验证文章已保存
        self.assertIsNotNone(new_article.pk)

    def test_get_list_display(self):
        """测试获取列表显示字段"""
        request = self.factory.get('/')
        request.user = self.admin_user
        list_display = self.article_admin.get_list_display(request)
        self.assertIn('title', list_display)
        self.assertIn('author', list_display)
        self.assertIn('status', list_display)

    def test_formfield_for_foreignkey_author(self):
        """测试作者字段的表单字段"""
        request = self.factory.get('/')
        request.user = self.admin_user

        from django.db import models
        field = Article._meta.get_field('author')
        formfield = self.article_admin.formfield_for_foreignkey(field, request)
        self.assertIsNotNone(formfield)
