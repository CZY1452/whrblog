"""
核心工具函数测试用例
包括 Markdown 渲染等工具函数
"""
from django.test import TestCase

from core.utils import CommonMarkdown


class CoreUtilsTest(TestCase):
    """测试核心工具函数"""

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
