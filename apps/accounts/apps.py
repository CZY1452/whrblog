import os
import shutil

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'apps.accounts'

    def ready(self):
        self._ensure_default_avatar()

    def _ensure_default_avatar(self):
        # 默认头像源文件随代码入库（apps/accounts/static/accounts/default_avatar.png），
        # 新服务器部署后首次启动自动复制进 MEDIA_ROOT/avatar/1.png，
        # 保证默认头像在所有环境都可用（uploads/ 不入库，不会随 git 下发）。
        try:
            from django.conf import settings
        except Exception:
            return
        src = os.path.join(os.path.dirname(__file__), 'static', 'accounts', 'default_avatar.png')
        if not os.path.exists(src):
            return
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatar')
        dst = os.path.join(avatar_dir, '1.png')
        if not os.path.exists(dst):
            os.makedirs(avatar_dir, exist_ok=True)
            shutil.copyfile(src, dst)
