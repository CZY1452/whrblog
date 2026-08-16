"""
Test cases for core utility functions
包括 SHA256、Markdown 渲染、URL 参数解析等工具函数
"""
from django.test import TestCase

from core.utils import get_sha256, CommonMarkdown, parse_dict_to_url


class CoreUtilsTest(TestCase):
    """测试核心工具函数"""

    def test_get_sha256(self):
        """测试 SHA256 哈希计算"""
        result = get_sha256('test')
        self.assertIsNotNone(result)

    def test_common_markdown_render(self):
        """测试 Markdown 渲染"""
        html = CommonMarkdown.get_markdown('''
        # Title1

        ```python
        import os
        ```

        [url](https://www.example.com/)

        [ddd](http://www.baidu.com)


        ''')
        self.assertIsNotNone(html)

    def test_parse_dict_to_url(self):
        """测试字典转 URL 参数"""
        d = {
            'd': 'key1',
            'd2': 'key2'
        }
        data = parse_dict_to_url(d)
        self.assertIsNotNone(data)
