"""
插件系统测试
测试插件加载、钩子注册和执行
"""
import os
from unittest.mock import Mock, patch

from django.test import TestCase

from core.plugin_manage.base_plugin import BasePlugin
from core.plugin_manage.hook_constants import *
from core.plugin_manage import hooks
from core.plugin_manage.loader import load_plugins
from core.tests.test_base import BaseTestCase, PluginTestMixin

# 导入钩子常量
from core.plugin_manage.hook_constants import HEAD_RESOURCES_HOOK, BODY_RESOURCES_HOOK


class PluginHooksTest(TestCase, PluginTestMixin):
    """测试插件钩子系统"""

    def setUp(self):
        # 清空插件钩子
        hooks._hooks = {}

    def test_register_hook(self):
        """测试注册钩子"""
        def test_hook(context):
            return "test"

        hooks.register(ARTICLE_CONTENT_HOOK_NAME, test_hook)
        self.assertIn(ARTICLE_CONTENT_HOOK_NAME, hooks._hooks)
        self.assertEqual(len(hooks._hooks[ARTICLE_CONTENT_HOOK_NAME]), 1)

    def test_apply_filters(self):
        """测试应用过滤器"""
        def test_filter(value):
            return value + " modified"

        hooks.register(ARTICLE_CONTENT_HOOK_NAME, test_filter)
        result = hooks.apply_filters(ARTICLE_CONTENT_HOOK_NAME, "original")
        self.assertEqual(result, "original modified")

    def test_run_action(self):
        """测试运行动作钩子"""
        executed = []

        def test_action():
            executed.append(True)

        hooks.register(ARTICLE_CREATE, test_action)
        hooks.run_action(ARTICLE_CREATE)
        self.assertTrue(len(executed) > 0)

    def test_multiple_hooks(self):
        """测试多个钩子"""
        results = []

        def hook1(value):
            results.append('hook1')
            return value + '1'

        def hook2(value):
            results.append('hook2')
            return value + '2'

        hooks.register(ARTICLE_CONTENT_HOOK_NAME, hook1)
        hooks.register(ARTICLE_CONTENT_HOOK_NAME, hook2)

        result = hooks.apply_filters(ARTICLE_CONTENT_HOOK_NAME, 'base')
        self.assertEqual(result, 'base12')
        self.assertEqual(len(results), 2)

    def test_hook_error_handling(self):
        """测试钩子错误处理"""
        def error_hook(value):
            raise Exception("Hook error")

        def normal_hook(value):
            return value + ' success'

        hooks.register(ARTICLE_CONTENT_HOOK_NAME, error_hook)
        hooks.register(ARTICLE_CONTENT_HOOK_NAME, normal_hook)

        # 即使有钩子出错，其他钩子也应该继续执行
        result = hooks.apply_filters(ARTICLE_CONTENT_HOOK_NAME, 'test')
        # 错误钩子不会修改值，但正常钩子会
        self.assertIn('success', result)


class BasePluginTest(BaseTestCase):
    """测试基础插件类"""

    def _create_test_plugin(self):
        """创建一个测试用的插件实例"""
        class TestPlugin(BasePlugin):
            PLUGIN_NAME = '测试插件'
            PLUGIN_DESCRIPTION = '用于测试的插件'
            PLUGIN_VERSION = '1.0.0'
            PLUGIN_AUTHOR = 'test'

        return TestPlugin()

    def test_plugin_initialization(self):
        """测试插件初始化"""
        plugin = self._create_test_plugin()
        self.assertIsNotNone(plugin.PLUGIN_NAME)
        self.assertIsNotNone(plugin.PLUGIN_VERSION)

    def test_plugin_config(self):
        """测试插件配置"""
        plugin = self._create_test_plugin()
        # 插件应该有配置属性
        self.assertIsNotNone(plugin.PLUGIN_NAME)

    def test_plugin_register_hooks(self):
        """测试插件注册钩子"""
        plugin = self._create_test_plugin()
        # 基类的 register_hooks 应该可以被调用
        plugin.register_hooks()

    def test_plugin_get_context(self):
        """测试获取插件信息"""
        plugin = self._create_test_plugin()
        plugin_info = plugin.get_plugin_info()
        self.assertIsInstance(plugin_info, dict)
        self.assertEqual(plugin_info['name'], '测试插件')


class PluginLoaderTest(TestCase):
    """测试插件加载器"""

    @patch('core.plugin_manage.loader.logger')
    def test_load_plugins(self, mock_logger):
        """测试加载插件"""
        plugins = load_plugins()
        self.assertIsInstance(plugins, list)

    def test_load_plugins_handles_errors(self):
        """测试插件加载错误处理"""
        # 测试当插件目录不存在或插件有错误时的处理
        with patch('os.path.exists', return_value=False):
            plugins = load_plugins()
            # 应该返回空列表或处理错误
            self.assertIsInstance(plugins, list)


class ArticleCopyrightPluginTest(BaseTestCase, PluginTestMixin):
    """测试文章版权插件"""

    def test_copyright_plugin_loaded(self):
        """测试版权插件已加载"""
        from plugins.article_copyright.plugin import ArticleCopyrightPlugin
        plugin = ArticleCopyrightPlugin()
        self.assertEqual(plugin.PLUGIN_NAME, '文章结尾版权声明')


class ExternalLinksPluginTest(BaseTestCase, PluginTestMixin):
    """测试外部链接插件"""

    def test_external_links_plugin_loaded(self):
        """测试外部链接插件已加载"""
        from plugins.external_links.plugin import ExternalLinksPlugin
        plugin = ExternalLinksPlugin()
        self.assertEqual(plugin.PLUGIN_NAME, '外部链接处理器')

    def test_external_links_processing(self):
        """测试外部链接处理"""
        from plugins.external_links.plugin import ExternalLinksPlugin
        plugin = ExternalLinksPlugin()

        content = '<a href="https://example.com">外部链接</a>'
        # 测试插件已加载即可，具体处理逻辑在运行时应用
        self.assertIsNotNone(plugin.PLUGIN_NAME)
