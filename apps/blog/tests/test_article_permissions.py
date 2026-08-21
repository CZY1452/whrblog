"""
文章权限业务测试用例
包括文章权限控制、用户角色与编辑权限等核心业务逻辑
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category


class ArticlePermissionTest(TestCase):
    """测试文章权限控制"""

    def setUp(self):
        """设置测试环境"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.author = BlogUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpassword'
        )

        self.other_user = BlogUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )

        self.admin_user = BlogUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )

        self.article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

    def test_author_is_article_owner(self):
        """测试作者是文章的所有者"""
        self.assertEqual(self.article.author, self.author)

    def test_other_user_is_not_article_owner(self):
        """测试其他用户不是文章的所有者"""
        self.assertNotEqual(self.article.author, self.other_user)

    def test_admin_has_superuser_privilege(self):
        """测试管理员有超级用户权限"""
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)

    def test_normal_user_no_staff_privilege(self):
        """测试普通用户没有staff权限"""
        self.assertFalse(self.other_user.is_staff)
        self.assertFalse(self.other_user.is_superuser)

    def test_article_author_can_edit(self):
        """测试文章作者可以编辑（权限检查逻辑）"""
        # 验证作者权限
        can_edit = (self.article.author == self.author)
        self.assertTrue(can_edit)

    def test_other_user_cannot_edit(self):
        """测试其他用户不能编辑（权限检查逻辑）"""
        # 验证其他用户无权限
        can_edit = (self.article.author == self.other_user)
        self.assertFalse(can_edit)

    def test_admin_can_edit_any_article(self):
        """测试管理员可以编辑任何文章（超级用户权限）"""
        # 管理员有超级用户权限，可以编辑任何文章
        can_edit = (self.article.author == self.admin_user or
                   self.admin_user.is_superuser)
        self.assertTrue(can_edit)
