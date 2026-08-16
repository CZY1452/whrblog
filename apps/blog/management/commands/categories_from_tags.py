"""将知识库导入产生的扁平分类重构为两级分类层级。

知识库导入时，子目录名作为 Tag、文章挂在主题（父分类）下。
本命令把每个 Tag 转成父分类下的子分类，并把对应文章移动到子分类，
随后清理这些转载生成的 Tag。

用法:
  manage.py categories_from_tags [--keep-tags]
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Article, Category, Tag


class Command(BaseCommand):
    help = '将 Tag 子目录重构为分类层级并迁移文章'

    def add_arguments(self, parser):
        parser.add_argument('--keep-tags', action='store_true', help='保留原标签不删除')

    @transaction.atomic
    def handle(self, *args, **options):
        parents = list(Category.objects.filter(parent_category__isnull=True))
        mapping = {}
        for parent in parents:
            for tag in Tag.objects.all():
                arts = list(Article.objects.filter(category=parent, tags=tag))
                if not arts:
                    continue
                child = Category.objects.filter(name=tag.name).first()
                if not child:
                    child = Category.objects.create(
                        name=tag.name,
                        parent_category=parent,
                        slug=tag.slug,
                        index=0,
                    )
                    self.stdout.write(f'创建子分类: {parent.name} > {child.name}')
                mapping.setdefault(child.id, []).extend(a.id for a in arts)

        for child_id, article_ids in mapping.items():
            Article.objects.filter(id__in=article_ids).update(
                category_id=child_id)
        self.stdout.write(f'已移动 {sum(len(v) for v in mapping.values())} 篇文章到子分类')

        for tag in Tag.objects.all():
            tag.article_set.clear()
        if options['keep_tags']:
            self.stdout.write('保留标签记录（已清空文章关联）')
        else:
            deleted, _ = Tag.objects.all().delete()
            self.stdout.write(f'已删除转载标签 {deleted} 条')

        count = Category.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'完成，当前分类总数: {count}（父分类 {len(parents)} 个）'))