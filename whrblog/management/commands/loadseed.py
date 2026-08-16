"""首次部署时自动灌入示例数据（文章/分类/管理员等）。

幂等：仅当数据库为空（无 Article 记录）时才导入，重复执行不会重复灌数据。

种子文件 deploy/seed/seed.json 由以下命令生成（纯 PK、按依赖重排，确保外键先被加载）：
    python manage.py dumpdata accounts blog comments servermanager --indent 2
并在提交前按 `Category / BlogUser → BlogSettings → Article` 的顺序排序。
文件随仓库分发，并在 docker-compose 中挂载进容器 /app/seed。
"""
import os

from django.apps import apps
from django.core.management import BaseCommand, call_command

SEED_PATH = os.environ.get("SEED_JSON_PATH", "/app/seed/seed.json")


class Command(BaseCommand):
    help = "If the database is empty, load the bundled seed fixture."

    def handle(self, *args, **options):
        Article = apps.get_model("blog", "Article")
        if Article.objects.exists():
            self.stdout.write(self.style.WARNING(
                "数据库中已有文章，跳过种子导入（seed already present）。"
            ))
            return

        if not os.path.exists(SEED_PATH):
            self.stdout.write(self.style.WARNING(
                f"未找到种子文件 {SEED_PATH}，跳过（如需示例数据请挂载 deploy/seed）。"
            ))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("正在导入种子数据 ..."))
        call_command("loaddata", SEED_PATH)
        self.stdout.write(self.style.SUCCESS(
            f"种子数据导入完成（来源：{SEED_PATH}）。"
        ))
