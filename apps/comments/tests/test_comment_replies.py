"""
评论回复与嵌套结构测试用例
包括评论回复和嵌套结构相关测试
"""
from django.test import TestCase

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category
from apps.comments.models import Comment


class CommentReplyTest(TestCase):
    """测试评论回复业务逻辑"""

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

        self.commenter1 = BlogUser.objects.create_user(
            username='commenter1',
            email='commenter1@example.com',
            password='password'
        )

        self.commenter2 = BlogUser.objects.create_user(
            username='commenter2',
            email='commenter2@example.com',
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

    def test_comment_can_have_no_parent(self):
        """测试评论可以没有父评论（根评论）"""
        comment = Comment.objects.create(
            body='Root comment',
            author=self.commenter1,
            article=self.article,
            parent_comment=None
        )

        self.assertIsNone(comment.parent_comment)

    def test_comment_can_have_parent(self):
        """测试评论可以有父评论（回复）"""
        parent_comment = Comment.objects.create(
            body='Parent comment',
            author=self.commenter1,
            article=self.article,
            is_enable=True
        )

        reply_comment = Comment.objects.create(
            body='Reply comment',
            author=self.commenter2,
            article=self.article,
            parent_comment=parent_comment,
            is_enable=True
        )

        self.assertEqual(reply_comment.parent_comment, parent_comment)

    def test_parent_comment_has_replies(self):
        """测试父评论有回复"""
        parent_comment = Comment.objects.create(
            body='Parent comment',
            author=self.commenter1,
            article=self.article,
            is_enable=True
        )

        reply1 = Comment.objects.create(
            body='Reply 1',
            author=self.commenter2,
            article=self.article,
            parent_comment=parent_comment,
            is_enable=True
        )

        reply2 = Comment.objects.create(
            body='Reply 2',
            author=self.commenter1,
            article=self.article,
            parent_comment=parent_comment,
            is_enable=True
        )

        # 查询父评论的所有回复
        replies = Comment.objects.filter(parent_comment=parent_comment)

        self.assertEqual(replies.count(), 2)
        self.assertIn(reply1, replies)
        self.assertIn(reply2, replies)

    def test_nested_comment_structure(self):
        """测试嵌套评论结构"""
        # 创建根评论
        root = Comment.objects.create(
            body='Root',
            author=self.commenter1,
            article=self.article,
            is_enable=True
        )

        # 创建一级回复
        level1 = Comment.objects.create(
            body='Level 1',
            author=self.commenter2,
            article=self.article,
            parent_comment=root,
            is_enable=True
        )

        # 创建二级回复
        level2 = Comment.objects.create(
            body='Level 2',
            author=self.commenter1,
            article=self.article,
            parent_comment=level1,
            is_enable=True
        )

        # 验证嵌套关系
        self.assertIsNone(root.parent_comment)
        self.assertEqual(level1.parent_comment, root)
        self.assertEqual(level2.parent_comment, level1)

    def test_multiple_replies_to_same_comment(self):
        """测试同一评论的多个回复"""
        parent = Comment.objects.create(
            body='Parent',
            author=self.commenter1,
            article=self.article,
            is_enable=True
        )

        # 创建多个回复
        replies = []
        for i in range(5):
            reply = Comment.objects.create(
                body=f'Reply {i+1}',
                author=self.commenter2,
                article=self.article,
                parent_comment=parent,
                is_enable=True
            )
            replies.append(reply)

        # 验证所有回复都关联到同一父评论
        parent_replies = Comment.objects.filter(parent_comment=parent)
        self.assertEqual(parent_replies.count(), 5)

        for reply in replies:
            self.assertIn(reply, parent_replies)
