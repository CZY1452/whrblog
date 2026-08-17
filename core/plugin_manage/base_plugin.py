import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BasePlugin:
    # 插件元数据
    PLUGIN_NAME = None
    PLUGIN_DESCRIPTION = None
    PLUGIN_VERSION = None
    PLUGIN_AUTHOR = None

    def __init__(self):
        if not all([self.PLUGIN_NAME, self.PLUGIN_DESCRIPTION, self.PLUGIN_VERSION]):
            raise ValueError("Plugin metadata (PLUGIN_NAME, PLUGIN_DESCRIPTION, PLUGIN_VERSION) must be defined.")

        # 设置插件路径
        self.plugin_dir = self._get_plugin_directory()
        self.plugin_slug = self._get_plugin_slug()

        self.init_plugin()
        self.register_hooks()

    def _get_plugin_directory(self):
        """获取插件目录路径"""
        import inspect
        plugin_file = inspect.getfile(self.__class__)
        return Path(plugin_file).parent

    def _get_plugin_slug(self):
        """获取插件标识符（目录名）"""
        return self.plugin_dir.name

    def init_plugin(self):
        """
        插件初始化逻辑
        子类可以重写此方法来实现特定的初始化操作
        """
        logger.info(f'{self.PLUGIN_NAME} initialized.')

    def register_hooks(self):
        """
        注册插件钩子
        子类可以重写此方法来注册特定的钩子
        """
        pass