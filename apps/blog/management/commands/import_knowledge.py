"""从 Markdown 知识库目录导入文章。

用法：
  manage.py import_knowledge <root> --admin-password <pwd> [--admin-user admin] [--admin-email '']

规则:
  - 根目录下 01-xxx ~ 05-xxx 编号目录视为主题，去掉数字前缀作为分类名
  - 每个 .md 文件生成一篇文章，标题为文件名；重名时加主题前缀
  - 主题目录内的子目录名作为标签
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from apps.blog.models import Article, Category, Tag

THEME_DIRNAMES = ['01-Python', '02-Django', '03-MySQL', '04-Redis', '05-Celery']


class Command(BaseCommand):
    help = '导入 Markdown 知识库为博客文章'

    def add_arguments(self, parser):
        parser.add_argument('root', type=str, help='知识库根目录')
        parser.add_argument('--admin-user', default='admin')
        parser.add_argument('--admin-password', required=True)
        parser.add_argument('--admin-email', default='')

    def handle(self, *args, **options):
        root = os.path.abspath(options['root'])
        if not os.path.isdir(root):
            raise CommandError(f'目录不存在: {root}')

        User = get_user_model()
        admin = User.objects.filter(username=options['admin_user']).first()
        if not admin:
            admin = User.objects.create_superuser(
                username=options['admin_user'],
                email=options['admin_email'],
                password=options['admin_password'])
            self.stdout.write(self.style.SUCCESS(
                f'已创建超级用户: {admin.username}'))

        imported = skipped = 0
        for dirname in THEME_DIRNAMES:
            theme_dir = os.path.join(root, dirname)
            if not os.path.isdir(theme_dir):
                self.stdout.write(self.style.WARNING(
                    f'跳过不存在的主题目录: {dirname}'))
                continue
            display = dirname.split('-', 1)[1]
            category, _ = Category.objects.get_or_create(
                name=display, defaults={'slug': display.lower(), 'index': 0})

            for dirpath, dirnames, filenames in os.walk(theme_dir):
                dirnames.sort()
                rel_dir = os.path.relpath(dirpath, theme_dir)
                tag = None
                if rel_dir != '.':
                    tag_name = os.path.basename(rel_dir)
                    tag, _ = Tag.objects.get_or_create(
                        name=tag_name, defaults={'slug': tag_name})
                for fname in sorted(filenames):
                    if not fname.endswith('.md'):
                        continue
                    title = os.path.splitext(fname)[0]
                    if Article.objects.filter(title=title).exists():
                        title = f'{display}-{title}'
                        if Article.objects.filter(title=title).exists():
                            title = f'{dirname}-{title}'
                    with open(os.path.join(dirpath, fname), encoding='utf-8') as f:
                        body = f.read()
                    if not body.strip():
                        skipped += 1
                        continue
                    article = Article.objects.create(
                        title=title,
                        body=body,
                        status='p',
                        type='a',
                        comment_status='o',
                        pub_time=now(),
                        show_toc=True,
                        author=admin,
                        category=category)
                    if tag:
                        article.tags.add(tag)
                    imported += 1

        self.stdout.write(self.style.SUCCESS(
            f'导入完成: 新增 {imported} 篇, 跳过空文件 {skipped} 个'))