"""文章 Markdown 导出功能测试"""
import io
import zipfile

from core.tests.test_base import BaseTestCase


class ArticleExportTest(BaseTestCase):
    """单篇文章导出测试"""

    def test_export_single_article(self):
        """导出单篇文章返回 .md 文件"""
        self.article.tags.add(self.tag)
        url = f'/api/articles/{self.article.id}/export/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/markdown', response['Content-Type'])
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('UTF-8', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertIn('---', content)
        self.assertIn(f'title: "{self.article.title}"', content)
        self.assertIn(f'category: "{self.category.name}"', content)
        self.assertIn(self.tag.name, content)
        self.assertIn(self.article.body, content)

    def test_export_article_without_tags(self):
        """导出无标签文章"""
        url = f'/api/articles/{self.article.id}/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertIn('tags: []', content)

    def test_export_nonexistent_article(self):
        """导出不存在的文章返回 404"""
        url = '/api/articles/99999/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ArticleBatchExportTest(BaseTestCase):
    """批量文章导出测试"""

    def test_batch_export(self):
        """批量导出返回 .zip 文件"""
        article2 = self.create_article(title='第二篇文章', body='第二篇内容')
        self.article.tags.add(self.tag)

        url = '/api/articles/export/'
        response = self.client.get(url, {'ids': f'{self.article.id},{article2.id}'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])

        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 2)
            self.assertIn(f'{self.article.title}.md', names)
            self.assertIn(f'{article2.title}.md', names)

            content = zf.read(f'{self.article.title}.md').decode('utf-8')
            self.assertIn(self.article.body, content)

    def test_batch_export_no_ids(self):
        """批量导出缺少 ids 参数返回 400"""
        url = '/api/articles/export/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    def test_batch_export_invalid_ids(self):
        """批量导出无效 ids 格式返回 400"""
        url = '/api/articles/export/'
        response = self.client.get(url, {'ids': 'abc,def'})
        self.assertEqual(response.status_code, 400)

    def test_batch_export_nonexistent_ids(self):
        """批量导出不存在的文章返回 404"""
        url = '/api/articles/export/'
        response = self.client.get(url, {'ids': '99998,99999'})
        self.assertEqual(response.status_code, 404)

    def test_batch_export_skips_drafts(self):
        """批量导出只包含已发布文章"""
        draft = self.create_article(title='草稿文章', body='草稿内容', status='d')
        url = '/api/articles/export/'
        response = self.client.get(url, {'ids': f'{self.article.id},{draft.id}'})

        self.assertEqual(response.status_code, 200)
        buf = io.BytesIO(response.content)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 1)
            self.assertIn(f'{self.article.title}.md', names)
