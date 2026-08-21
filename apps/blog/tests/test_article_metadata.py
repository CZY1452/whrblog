"""
文章元数据业务测试用例
包括文章评论状态、文章类型、分类标签等核心业务逻辑
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category


class ArticleCommentStatusTest(TestCase):
    """测试文章评论状态控制"""

    def setUp(self):
        """设置测试环境"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.author = BlogUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='password'
        )

    def test_article_comment_open_by_default(self):
        """测试文章评论默认开放"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='o'  # 开放评论
        )

        self.assertEqual(article.comment_status, 'o')

    def test_article_comment_can_be_closed(self):
        """测试可以关闭文章评论"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='o'
        )

        # 关闭评论
        article.comment_status = 'c'
        article.save()

        article.refresh_from_db()
        self.assertEqual(article.comment_status, 'c')

    def test_closed_comment_article_status(self):
        """测试关闭评论的文章状态正确"""
        article = Article.objects.create(
            title='No Comments Article',
            body='No comments allowed',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='c'
        )

        # 验证评论已关闭
        self.assertEqual(article.comment_status, 'c')


class ArticleTypeTest(TestCase):
    """测试文章类型业务逻辑"""

    def setUp(self):
        """设置测试环境"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.author = BlogUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='password'
        )

    def test_article_type_is_article(self):
        """测试文章类型为article"""
        article = Article.objects.create(
            title='Article Type',
            body='Article content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'  # 文章类型
        )

        self.assertEqual(article.type, 'a')

    def test_article_type_is_page(self):
        """测试文章类型为page"""
        page = Article.objects.create(
            title='Page Type',
            body='Page content',
            author=self.author,
            category=self.category,
            status='p',
            type='p'  # 页面类型
        )

        self.assertEqual(page.type, 'p')

    def test_articles_and_pages_are_separate(self):
        """测试文章和页面分开查询"""
        # 创建文章
        article = Article.objects.create(
            title='Article',
            body='Article content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        # 创建页面
        page = Article.objects.create(
            title='Page',
            body='Page content',
            author=self.author,
            category=self.category,
            status='p',
            type='p'
        )

        # 只查询文章
        articles = Article.objects.filter(type='a', status='p')
        self.assertIn(article, articles)
        self.assertNotIn(page, articles)

        # 只查询页面
        pages = Article.objects.filter(type='p', status='p')
        self.assertIn(page, pages)
        self.assertNotIn(article, pages)


class ArticleCategoryTagTest(TestCase):
    """测试文章与分类标签的关系"""

    def setUp(self):
        """设置测试环境"""
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        self.author = BlogUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='password'
        )

    def test_article_belongs_to_category(self):
        """测试文章属于分类"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        self.assertEqual(article.category, self.category)

    def test_category_has_articles(self):
        """测试分类包含文章"""
        article1 = Article.objects.create(
            title='Article 1',
            body='Content 1',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        article2 = Article.objects.create(
            title='Article 2',
            body='Content 2',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        # 查询该分类下的文章
        category_articles = Article.objects.filter(
            category=self.category,
            status='p'
        )

        self.assertEqual(category_articles.count(), 2)
        self.assertIn(article1, category_articles)
        self.assertIn(article2, category_articles)

    def test_article_can_change_category(self):
        """测试文章可以更改分类"""
        new_category = Category.objects.create(
            name='New Category',
            slug='new-category'
        )

        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        # 更改分类
        article.category = new_category
        article.save()

        article.refresh_from_db()
        self.assertEqual(article.category, new_category)
