"""将一级（主题）分类设为标签，并给其分类树下的所有文章添加该标签。

用法：
  manage.py add_theme_tags

说明：
  - 每个根分类创建一个同名标签（如 Python、Django）
  - 给该分类下所有层级（含子分类）的文章打上标签
  - 幂等，可重复执行
"""
from django.core.management.base import BaseCommand

from apps.blog.models import Category
from .import_knowledge import ensure_theme_tag


class Command(BaseCommand):
    help = '将一级主题分类设为标签并给所有子文章添加'

    def handle(self, *args, **options):
        roots = list(Category.objects.filter(parent_category=None))
        total_articles = 0
        for category in roots:
            tagged = ensure_theme_tag(category)
            self.stdout.write(self.style.SUCCESS(
                f'标签「{category.name}」: 已给 {tagged} 篇文章打标'))
            total_articles += tagged
        self.stdout.write(self.style.SUCCESS(
            f'完成: {len(roots)} 个主题标签, 共 {total_articles} 篇文章'))