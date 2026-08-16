"""
重建 Elasticsearch 索引
用法：python manage.py rebuild_es_index [--no-delete]
"""
import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '重建 Elasticsearch 索引：删除旧索引、创建新索引、全量导入已发布文章'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-delete',
            action='store_true',
            default=False,
            help='不删除旧索引，仅追加索引（索引已存在时报错）',
        )

    def handle(self, *args, **options):
        from core.es_client import (
            recreate_index, ensure_index, bulk_index_articles, is_available,
        )
        from apps.blog.models import Article

        # 检查 ES 连接
        self.stdout.write('检查 Elasticsearch 连接...')
        if not is_available():
            self.stderr.write(self.style.ERROR(
                '无法连接到 Elasticsearch，请检查 ES 服务是否已启动'))
            return

        self.stdout.write(self.style.SUCCESS('ES 连接正常'))

        # 创建/重建索引
        if options['no_delete']:
            self.stdout.write('确保索引存在...')
            ensure_index()
        else:
            self.stdout.write('重建索引（删除旧索引）...')
            recreate_index()

        # 全量导入已发布文章
        self.stdout.write('开始导入已发布文章...')
        articles = Article.objects.filter(
            status='p', type='a'
        ).select_related(
            'author', 'category'
        ).prefetch_related('tags')

        total = articles.count()
        self.stdout.write(f'共 {total} 篇已发布文章')

        count = bulk_index_articles(articles)
        self.stdout.write(self.style.SUCCESS(
            f'索引重建完成，共导入 {count} 篇文章'))
