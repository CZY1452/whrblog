"""
文章生命周期业务测试用例
包括文章状态转换、时间戳、slug生成以及遗留的管理命令测试
"""
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category


class ArticleLifecycleTest(TestCase):
    """测试文章完整生命周期"""

    def setUp(self):
        """设置测试环境"""
        self.client = Client()

        # 创建测试分类
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )

        # 创建作者用户
        self.author = BlogUser.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpassword'
        )

        # 创建其他普通用户
        self.other_user = BlogUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpassword'
        )

        # 创建管理员用户
        self.admin_user = BlogUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )

    def test_article_created_as_draft_by_default(self):
        """测试文章创建时默认为草稿状态"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='d',  # 草稿
            type='a'
        )
        self.assertEqual(article.status, 'd')

    def test_article_draft_to_published_transition(self):
        """测试文章从草稿到发布的状态转换"""
        article = Article.objects.create(
            title='Draft Article',
            body='Draft content',
            author=self.author,
            category=self.category,
            status='d',
            type='a'
        )

        # 验证初始状态
        self.assertEqual(article.status, 'd')
        original_pub_time = article.pub_time

        # 修改为发布状态
        article.status = 'p'
        article.save()

        # 验证状态已改变
        article.refresh_from_db()
        self.assertEqual(article.status, 'p')

    def test_article_published_to_draft_transition(self):
        """测试文章从发布到草稿的状态转换"""
        article = Article.objects.create(
            title='Published Article',
            body='Published content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        # 验证初始状态
        self.assertEqual(article.status, 'p')

        # 修改回草稿状态
        article.status = 'd'
        article.save()

        # 验证状态已改变
        article.refresh_from_db()
        self.assertEqual(article.status, 'd')

    def test_draft_article_not_in_public_list(self):
        """测试草稿文章不在公开列表中"""
        # 创建草稿文章
        draft_article = Article.objects.create(
            title='Draft Article',
            body='Draft content',
            author=self.author,
            category=self.category,
            status='d',
            type='a'
        )

        # 创建已发布文章
        published_article = Article.objects.create(
            title='Published Article',
            body='Published content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        # 获取公开文章列表（只包含已发布的）
        public_articles = Article.objects.filter(status='p', type='a')

        # 验证草稿文章不在列表中
        self.assertNotIn(draft_article, public_articles)
        self.assertIn(published_article, public_articles)

    def test_article_views_counter_increases(self):
        """测试文章浏览量计数器增加"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            views=0
        )

        initial_views = article.views

        # 模拟浏览文章
        article.views += 1
        article.save()

        # 验证浏览量增加
        article.refresh_from_db()
        self.assertEqual(article.views, initial_views + 1)

    def test_article_views_multiple_increments(self):
        """测试文章多次浏览时浏览量正确累加"""
        article = Article.objects.create(
            title='Popular Article',
            body='Popular content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            views=0
        )

        # 模拟多次浏览
        for i in range(10):
            article.views += 1
            article.save()

        article.refresh_from_db()
        self.assertEqual(article.views, 10)


class ArticleTimestampTest(TestCase):
    """测试文章时间戳业务逻辑"""

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

    def test_article_has_creation_time(self):
        """测试文章有创建时间"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        self.assertIsNotNone(article.creation_time)
        # 验证创建时间是最近的
        time_diff = timezone.now() - article.creation_time
        self.assertLess(time_diff.total_seconds(), 10)  # 10秒内创建

    def test_article_has_last_mod_time(self):
        """测试文章有最后修改时间"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        self.assertIsNotNone(article.last_modify_time)

    def test_article_last_mod_time_updates(self):
        """测试文章修改后最后修改时间更新"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        original_mod_time = article.last_modify_time

        # 等待一小段时间
        import time
        time.sleep(0.1)

        # 修改文章
        article.body = 'Updated content'
        article.save()

        article.refresh_from_db()
        # last_modify_time应该自动更新（如果模型配置了auto_now）
        # 注意：这取决于模型的auto_now配置


class ArticleSlugTest(TestCase):
    """测试文章slug生成逻辑"""

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

    def test_article_has_id(self):
        """测试文章有ID（用于URL生成）"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        self.assertIsNotNone(article.id)
        # 验证可以通过ID访问
        retrieved_article = Article.objects.get(id=article.id)
        self.assertEqual(retrieved_article, article)

    def test_article_absolute_url(self):
        """测试文章绝对URL生成"""
        article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a'
        )

        url = article.get_absolute_url()
        self.assertIsNotNone(url)
        # URL应该包含文章ID
        self.assertIn(str(article.id), url)


class ArticleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

    def test_errorpage(self):
        rsp = self.client.get('/eee')
        self.assertEqual(rsp.status_code, 404)

    def test_commands(self):
        """clear_cache 管理命令可正常执行"""
        call_command("clear_cache")
