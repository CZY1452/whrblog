"""
Blog 公开 API 测试
覆盖前端化页面对应的数据端点：链接 / 搜索
"""
from django.urls import reverse

from core.tests.test_base import BaseTestCase


class LinksApiTest(BaseTestCase):
    """友情链接 API"""

    def test_links_returns_enabled_links(self):
        from apps.blog.models import Links
        Links.objects.create(name='测试友链', link='https://example.com', sequence=1, is_enable=True)
        response = self.client.get('/api/links/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        results = data['results']
        self.assertGreater(len(results), 0)
        self.assertIn('name', results[0])
        self.assertIn('link', results[0])


class SearchApiTest(BaseTestCase):
    """搜索 API"""

    def test_search_returns_matches(self):
        self.create_article(title='Django 最佳实践教程')
        response = self.client.get('/api/search/', {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['query'], 'Django')
        self.assertIsInstance(data['results'], list)
        self.assertGreater(len(data['results']), 0)
        self.assertEqual(data['results'][0]['title'], 'Django 最佳实践教程')

    def test_search_empty_query(self):
        response = self.client.get('/api/search/', {'q': ''})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])

    def test_search_no_matches(self):
        response = self.client.get('/api/search/', {'q': '不存在的关键词xyz'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['results'], [])
