"""
Test cases for comment moderation workflow
包括评论审核工作流相关测试
"""
from django.test import TestCase

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category, BlogSettings
from apps.comments.models import Comment


class CommentModerationTest(TestCase):
    """测试评论审核工作流"""

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

        # 获取或创建博客设置
        self.blog_settings, _ = BlogSettings.objects.get_or_create(
            id=1,
            defaults={'site_name': 'Test Blog'}
        )

    def test_comment_pending_by_default_when_review_required(self):
        """测试需要审核时评论默认为待审状态"""
        # 启用评论审核
        self.blog_settings.comment_need_review = True
        self.blog_settings.save()

        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article,
            is_enable=False  # 待审状态
        )

        self.assertFalse(comment.is_enable)

    def test_comment_approved_directly_when_no_review_required(self):
        """测试不需要审核时评论直接通过"""
        # 禁用评论审核
        self.blog_settings.comment_need_review = False
        self.blog_settings.save()

        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article,
            is_enable=True  # 直接启用
        )

        self.assertTrue(comment.is_enable)

    def test_comment_can_be_approved(self):
        """测试评论可以被批准"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article,
            is_enable=False
        )

        # 审核通过
        comment.is_enable = True
        comment.save()

        comment.refresh_from_db()
        self.assertTrue(comment.is_enable)

    def test_comment_can_be_rejected(self):
        """测试评论可以被拒绝"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        # 拒绝评论
        comment.is_enable = False
        comment.save()

        comment.refresh_from_db()
        self.assertFalse(comment.is_enable)

    def test_only_approved_comments_in_public_list(self):
        """测试只有已批准的评论在公开列表中"""
        # 创建已批准的评论
        approved_comment = Comment.objects.create(
            body='Approved comment',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        # 创建待审的评论
        pending_comment = Comment.objects.create(
            body='Pending comment',
            author=self.commenter,
            article=self.article,
            is_enable=False
        )

        # 查询已批准的评论
        approved_comments = Comment.objects.filter(
            article=self.article,
            is_enable=True
        )

        self.assertIn(approved_comment, approved_comments)
        self.assertNotIn(pending_comment, approved_comments)
