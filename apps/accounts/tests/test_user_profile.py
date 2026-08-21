"""
用户资料、查询与删除业务逻辑测试用例
包括用户资料管理、查询操作、删除等核心业务逻辑
"""
from django.test import TestCase

from apps.accounts.models import BlogUser


class UserProfileTest(TestCase):
    """测试用户资料业务逻辑"""

    def test_user_has_username(self):
        """测试用户有用户名"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        self.assertEqual(user.username, 'testuser')

    def test_user_has_email(self):
        """测试用户有邮箱"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        self.assertEqual(user.email, 'test@example.com')

    def test_user_can_update_email(self):
        """测试用户可以更新邮箱"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='old@example.com',
            password='password'
        )

        new_email = 'new@example.com'
        user.email = new_email
        user.save()

        user.refresh_from_db()
        self.assertEqual(user.email, new_email)

    def test_user_string_representation(self):
        """测试用户字符串表示"""
        user = BlogUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )

        # __str__ 方法应该返回用户名或有意义的字符串
        user_str = str(user)
        self.assertIsInstance(user_str, str)
        self.assertTrue(len(user_str) > 0)


class UserQueryTest(TestCase):
    """测试用户查询业务逻辑"""

    def setUp(self):
        """设置测试环境"""
        # 创建多个用户
        self.users = []
        for i in range(5):
            user = BlogUser.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password'
            )
            self.users.append(user)

    def test_query_user_by_username(self):
        """测试按用户名查询用户"""
        user = BlogUser.objects.get(username='user0')
        self.assertEqual(user, self.users[0])

    def test_query_user_by_email(self):
        """测试按邮箱查询用户"""
        user = BlogUser.objects.get(email='user1@example.com')
        self.assertEqual(user, self.users[1])

    def test_query_active_users(self):
        """测试查询激活的用户"""
        # 停用一些用户
        self.users[0].is_active = False
        self.users[0].save()
        self.users[1].is_active = False
        self.users[1].save()

        # 查询激活的用户
        active_users = BlogUser.objects.filter(is_active=True)
        self.assertEqual(active_users.count(), 3)

    def test_query_staff_users(self):
        """测试查询staff用户"""
        # 提升一些用户为staff
        self.users[0].is_staff = True
        self.users[0].save()
        self.users[1].is_staff = True
        self.users[1].save()

        # 查询staff用户
        staff_users = BlogUser.objects.filter(is_staff=True)
        self.assertEqual(staff_users.count(), 2)

    def test_query_superusers(self):
        """测试查询超级用户"""
        # 创建超级用户
        BlogUser.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )

        # 查询超级用户
        superusers = BlogUser.objects.filter(is_superuser=True)
        self.assertEqual(superusers.count(), 1)


class UserDeletionTest(TestCase):
    """测试用户删除业务逻辑"""

    def test_user_can_be_deleted(self):
        """测试用户可以被删除"""
        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )

        user_id = user.id

        # 删除用户
        user.delete()

        # 验证用户已被删除
        with self.assertRaises(BlogUser.DoesNotExist):
            BlogUser.objects.get(id=user_id)

    def test_delete_user_cascade_effects(self):
        """测试删除用户的级联效果"""
        from apps.blog.models import Article, Category

        user = BlogUser.objects.create_user(
            username='user',
            email='user@example.com',
            password='password'
        )

        # 创建用户的文章
        category = Category.objects.create(
            name='Category',
            slug='category'
        )

        article = Article.objects.create(
            title='User Article',
            body='Content',
            author=user,
            category=category,
            status='p',
            type='a'
        )

        article_id = article.id

        # 删除用户
        user.delete()

        # 验证文章的处理（取决于外键的on_delete设置）
        # 如果是CASCADE，文章应该被删除
        with self.assertRaises(Article.DoesNotExist):
            Article.objects.get(id=article_id)
