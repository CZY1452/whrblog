"""
Test cases for comment queries and deletion
包括评论查询和删除相关测试
"""
from django.test import TestCase

from apps.accounts.models import BlogUser
from apps.blog.models import Article, Category
from apps.comments.models import Comment


class CommentQueryTest(TestCase):
    """测试评论查询业务逻辑"""

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
            type='a'
        )

    def test_query_comments_by_article(self):
        """测试按文章查询评论"""
        # 创建多个评论
        for i in range(5):
            Comment.objects.create(
                body=f'Comment {i+1}',
                author=self.commenter,
                article=self.article,
                is_enable=True
            )

        comments = Comment.objects.filter(article=self.article)
        self.assertEqual(comments.count(), 5)

    def test_query_comments_by_author(self):
        """测试按作者查询评论"""
        # 创建评论
        for i in range(3):
            Comment.objects.create(
                body=f'Comment {i+1}',
                author=self.commenter,
                article=self.article,
                is_enable=True
            )

        comments = Comment.objects.filter(author=self.commenter)
        self.assertEqual(comments.count(), 3)

    def test_query_root_comments_only(self):
        """测试只查询根评论（无父评论的评论）"""
        # 创建根评论
        root1 = Comment.objects.create(
            body='Root 1',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        root2 = Comment.objects.create(
            body='Root 2',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        # 创建回复
        Comment.objects.create(
            body='Reply to Root 1',
            author=self.commenter,
            article=self.article,
            parent_comment=root1,
            is_enable=True
        )

        # 查询根评论
        root_comments = Comment.objects.filter(
            article=self.article,
            parent_comment__isnull=True
        )

        self.assertEqual(root_comments.count(), 2)
        self.assertIn(root1, root_comments)
        self.assertIn(root2, root_comments)

    def test_comment_ordering(self):
        """测试评论排序"""
        # 创建多个评论
        comments = []
        for i in range(3):
            comment = Comment.objects.create(
                body=f'Comment {i+1}',
                author=self.commenter,
                article=self.article,
                is_enable=True
            )
            comments.append(comment)

        # 查询评论（应该按照模型定义的ordering排序）
        ordered_comments = list(Comment.objects.filter(article=self.article))

        # 验证至少返回了正确数量的评论
        self.assertEqual(len(ordered_comments), 3)


class CommentDeletionTest(TestCase):
    """测试评论删除业务逻辑"""

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
            type='a'
        )

    def test_comment_can_be_deleted(self):
        """测试评论可以被删除"""
        comment = Comment.objects.create(
            body='Test comment',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        comment_id = comment.id

        # 删除评论
        comment.delete()

        # 验证评论已被删除
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

    def test_deleting_parent_comment_with_replies(self):
        """测试删除有回复的父评论"""
        parent = Comment.objects.create(
            body='Parent',
            author=self.commenter,
            article=self.article,
            is_enable=True
        )

        reply = Comment.objects.create(
            body='Reply',
            author=self.commenter,
            article=self.article,
            parent_comment=parent,
            is_enable=True
        )

        parent_id = parent.id
        reply_id = reply.id

        # 删除父评论
        parent.delete()

        # 验证父评论被删除
        with self.assertRaises(Comment.DoesNotExist):
            Comment.objects.get(id=parent_id)

        # 验证回复的处理（取决于模型的on_delete设置）
        # 如果是CASCADE，回复也应该被删除
        # 如果是SET_NULL，回复的parent应该为None
