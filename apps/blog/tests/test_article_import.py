"""文章 Markdown 导入功能测试"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile

from core.tests.test_base import BaseTestCase


class ArticleImportTest(BaseTestCase):
    """文章导入测试"""

    def _upload(self, content, filename='test.md', login_admin=True):
        if login_admin:
            self.login_admin()
        md_file = SimpleUploadedFile(
            filename, content.encode('utf-8'), content_type='text/markdown'
        )
        return self.client.post('/api/articles/import/', {'file': md_file})

    def test_import_with_front_matter(self):
        """导入带 YAML front matter 的 .md 文件"""
        content = """---
title: "测试导入文章"
date: "2026-08-15 10:00"
category: "技术"
tags: [Python, Django]
---

# 测试导入文章

这是正文内容。
"""
        response = self._upload(content)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], '测试导入文章')
        self.assertEqual(data['category'], '技术')
        self.assertEqual(data['tags'], ['Python', 'Django'])
        self.assertEqual(data['date'], '2026-08-15 10:00')
        self.assertIn('这是正文内容。', data['body'])

    def test_import_plain_markdown_with_heading(self):
        """导入纯 Markdown 文件，从 # 标题提取标题"""
        content = """# 我的文章标题

这是纯 Markdown 内容，没有 front matter。
"""
        response = self._upload(content)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], '我的文章标题')
        self.assertIn('这是纯 Markdown 内容', data['body'])
        self.assertEqual(data['tags'], [])
        self.assertEqual(data['category'], '')

    def test_import_plain_markdown_no_heading(self):
        """导入纯 Markdown 无标题，从文件名推断"""
        content = '只有一些内容，没有标题。'
        response = self._upload(content, filename='我的笔记.md')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], '我的笔记')
        self.assertEqual(data['body'], content)

    def test_import_invalid_front_matter(self):
        """front matter 格式错误时降级为纯文本处理"""
        content = """---
title: [invalid yaml:::
---

正文内容
"""
        response = self._upload(content)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 降级后从正文的 # 标题或文件名推断
        self.assertTrue(len(data['title']) > 0)

    def test_import_no_file(self):
        """未上传文件返回 400"""
        self.login_admin()
        response = self.client.post('/api/articles/import/')
        self.assertEqual(response.status_code, 400)

    def test_import_wrong_extension(self):
        """上传非 .md 文件返回 400"""
        self.login_admin()
        txt_file = SimpleUploadedFile(
            'test.txt', b'hello', content_type='text/plain'
        )
        response = self.client.post('/api/articles/import/', {'file': txt_file})
        self.assertEqual(response.status_code, 400)

    def test_import_non_admin_forbidden(self):
        """非管理员无法导入"""
        self.login_user()
        md_file = SimpleUploadedFile(
            'test.md', b'# Hello\ncontent', content_type='text/markdown'
        )
        response = self.client.post('/api/articles/import/', {'file': md_file})
        self.assertIn(response.status_code, [401, 403])

    def test_import_tags_as_string(self):
        """tags 为逗号分隔字符串时正确解析"""
        content = """---
title: "标签测试"
tags: "Python, Django, Web"
---

正文
"""
        response = self._upload(content)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['tags'], ['Python', 'Django', 'Web'])
