"""
评论创建与文章状态关系测试用例hip
包括评论创建业务逻辑和评论与文章状态的关系
"""
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category
from apps.comments.models import Comment


class CommentCreationTest(TestCase):
    """测试评论创建业务逻辑"""

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

        self.commenter = BlogUser.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='password'
        )

        self.article = Article.objects.create(
            title='Test Article',
            body='Test content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='o'
        )

    def test_comment_created_with_required_fields(self):
        """测试评论创建包含必需字段"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article
        )

        self.assertIsNotNone(comment.id)
        self.assertEqual(comment.body, 'Test comment')
        self.assertEqual(comment.author, self.commenter)
        self.assertEqual(comment.article, self.article)

    def test_comment_has_creation_time(self):
        """测试评论有创建时间"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article
        )

        self.assertIsNotNone(comment.creation_time)
        # 验证创建时间是最近的
        time_diff = timezone.now() - comment.creation_time
        self.assertLess(time_diff.total_seconds(), 10)

    def test_comment_author_is_correct(self):
        """测试评论作者正确"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article
        )

        self.assertEqual(comment.author, self.commenter)

    def test_comment_article_relationship(self):
        """测试评论与文章的关系"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article
        )

        self.assertEqual(comment.article, self.article)
        # 验证可以通过文章查询到评论
        article_comments = Comment.objects.filter(article=self.article)
        self.assertIn(comment, article_comments)


class CommentArticleStatusTest(TestCase):
    """测试评论与文章状态的关系"""

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

        self.commenter = BlogUser.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='password'
        )

    def test_can_comment_on_open_comment_article(self):
        """测试可以在开放评论的文章上评论"""
        article = Article.objects.create(
            title='Open Comment Article',
            body='Content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='o'  # 开放评论
        )

        # 业务逻辑层面：评论状态开放
        self.assertEqual(article.comment_status, 'o')

        # 创建评论应该成功
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=article,
            is_enable=True
        )

        self.assertIsNotNone(comment.id)

    def test_comment_status_closed_validation(self):
        """测试关闭评论的文章状态"""
        article = Article.objects.create(
            title='Closed Comment Article',
            body='Content',
            author=self.author,
            category=self.category,
            status='p',
            type='a',
            comment_status='c'  # 关闭评论
        )

        # 验证文章评论状态
        self.assertEqual(article.comment_status, 'c')

        # 注意：实际的验证应该在视图层进行
        # 这里我们只测试模型层面的状态

    def test_comments_belong_to_correct_article(self):
        """测试评论属于正确的文章"""
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

        comment1 = Comment.objects.create(
            body='Comment on Article 1',
            author=self.commenter,
            article=article1,
            is_enable=True
        )

        comment2 = Comment.objects.create(
            body='Comment on Article 2',
            author=self.commenter,
            article=article2,
            is_enable=True
        )

        # 验证评论属于正确的文章
        article1_comments = Comment.objects.filter(article=article1)
        article2_comments = Comment.objects.filter(article=article2)

        self.assertIn(comment1, article1_comments)
        self.assertNotIn(comment2, article1_comments)

        self.assertIn(comment2, article2_comments)
        self.assertNotIn(comment1, article2_comments)
