from django.apps import AppConfig

class WhrblogAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'whrblog'

    def ready(self):
        super().ready()
        # 在此处加载插件
        from core.plugin_manage.loader import load_plugins
        load_plugins()

        # 注册信号接收器（ES 同步、缓存清理等）。
        # 注意：core.blog_signals 此前只在 send_email() 内部被惰性导入，
        # 若邮件功能从未使用，则 post_save/post_delete/m2m_changed 信号不会注册，
        # 导致文章新建/编辑后不自动同步到 ES、搜索遗漏。
        from core import blog_signals  # noqa: F401 