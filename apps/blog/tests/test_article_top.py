"""
置顶功能测试
覆盖 is_top 字段默认值、全站列表置顶排序、分类列表不置顶、序列化输出
"""
from datetime import timedelta

from django.utils import timezone

from apps.blog.models import Article, Category
from core.tests.test_base import BaseTestCase


def _ago(days):
    return timezone.now() - timedelta(days=days)


class ArticleTopModelTest(BaseTestCase):
    """Article 模型 is_top 字段"""

    def test_is_top_default_false(self):
        article = self.create_article(title='默认非置顶')
        self.assertFalse(article.is_top)

    def test_is_top_can_be_set_and_persisted(self):
        article = self.create_article(title='置顶文章')
        article.is_top = True
        article.save()
        article.refresh_from_db()
        self.assertTrue(article.is_top)


class ArticleTopApiTest(BaseTestCase):
    """全站文章列表置顶排序"""

    def setUp(self):
        super().setUp()
        # 移除基类自动创建的文章，避免影响排序断言
        self.article.delete()

    def test_list_response_includes_is_top(self):
        self.create_article(title='序列化文章')
        response = self.client.get('/api/articles/')
        results = response.json()['results']
        self.assertIn('is_top', results[0])

    def test_pinned_article_precedes_newer_normal_article(self):
        self.create_article(title='普通新文章', pub_time=timezone.now() + timedelta(days=1))
        pinned = self.create_article(title='置顶旧文章', pub_time=_ago(30))
        pinned.is_top = True
        pinned.save()

        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results[0]['title'], '置顶旧文章')
        self.assertTrue(results[0]['is_top'])

    def test_multiple_pinned_articles_ordered_by_pub_time(self):
        older = self.create_article(title='置顶甲', pub_time=_ago(5))
        newer = self.create_article(title='置顶乙', pub_time=_ago(2))
        older.is_top = True
        older.save()
        newer.is_top = True
        newer.save()

        response = self.client.get('/api/articles/')
        results = response.json()['results']
        top_titles = [r['title'] for r in results if r['is_top']]
        self.assertEqual(top_titles, ['置顶乙', '置顶甲'])

    def test_normal_articles_keep_pub_time_order(self):
        self.create_article(title='旧文章', pub_time=_ago(10))
        self.create_article(title='新文章', pub_time=timezone.now())

        response = self.client.get('/api/articles/')
        results = response.json()['results']
        self.assertEqual(results[0]['title'], '新文章')


class ArticleTopCategoryApiTest(BaseTestCase):
    """分类/标签列表保持原有排序，不做置顶"""

    def setUp(self):
        super().setUp()
        self.article.delete()

    def test_category_list_not_reordered_by_top_flag(self):
        cat = self.create_category(name='分类A')
        self.create_article(title='分类新文', category=cat, pub_time=timezone.now())
        pinned = self.create_article(title='分类置顶旧文', category=cat, pub_time=_ago(10))
        pinned.is_top = True
        pinned.save()

        response = self.client.get(f'/api/articles/?category={cat.slug}')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        # 分类列表不置顶排序，新文章在前
        self.assertEqual(results[0]['title'], '分类新文')
        # 但序列化仍携带 is_top 标识
        by_title = {r['title']: r for r in results}
        self.assertTrue(by_title['分类置顶旧文']['is_top'])

