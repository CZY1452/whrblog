"""从 Markdown 知识库目录导入文章，按原目录层级还原为分类树。

用法：
  manage.py import_knowledge <root> --admin-password <pwd> [--admin-user admin] [--admin-email '']

规则:
  - 根目录下的目录递归映射为分类树（最多 4 层），目录名去掉数字前缀作为分类名
  - 分类保留目录编号作为排序 index，编号越大越靠前
  - 每个 .md 文件生成一篇文章，标题为去掉数字前缀的文件名；
    重名时加父分类名作前缀
  - 文章归入其所在目录（最深）对应的分类
  - 空文件跳过；根目录直下的 .md 归入「未分类」
"""
import os
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.timezone import now

from apps.blog.models import Article, Category, Tag

MAX_LEVEL = 4
_ORDER_RE = re.compile(r'^(\d+)[-_ ]?(.*)$')


def _category_slug(name):
    """多级分类 slug：ASCII 转小写，中文保留原字符便于 URL 展示"""
    return name.lower() if name.isascii() else name


def ensure_theme_tag(category):
    """将一级（主题）分类设为同名标签，并给该分类树下的所有文章打上标签。幂等。"""
    tag, _ = Tag.objects.get_or_create(
        name=category.name, defaults={'slug': _category_slug(category.name)})
    article_ids = _collect_descendant_article_ids(category)
    articles = list(Article.objects.filter(id__in=article_ids))
    for article in articles:
        article.tags.add(tag)
    return len(articles)


def _collect_descendant_article_ids(category):
    """收集分类及其全部子分类下的文章 id"""
    ids = list(category.article_set.values_list('id', flat=True))
    for child in Category.objects.filter(parent_category=category):
        ids += _collect_descendant_article_ids(child)
    return ids


def _split_numbered(name, fallback=0):
    """解析 '01-基础语法' -> (1, '基础语法')；无编号则返回 (fallback, 原名)"""
    m = _ORDER_RE.match(name)
    if m and m.group(1):
        return (int(m.group(1)), m.group(2).strip() or name)
    return (fallback, name)


class Command(BaseCommand):
    help = '按原目录层级导入 Markdown 知识库为博客分类树与文章'

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

        self._title_keys = {
            t.lower() for t in Article.objects.values_list('title', flat=True)}
        imported = skipped = 0
        category_count = 0

        for entry in sorted(os.listdir(root), key=str.lower):
            path = os.path.join(root, entry)
            if os.path.isdir(path):
                category, cat_imported, cat_skipped = self._import_tree(
                    path, parent=None, level=1, admin=admin)
                if category:
                    category_count += 1
                    imported += cat_imported
                    skipped += cat_skipped
                    # 一级（主题）分类设为标签，给其树内所有文章打标
                    ensure_theme_tag(category)

        # 根目录直下的 .md 文件归入「未分类」
        for fname in sorted(os.listdir(root)):
            path = os.path.join(root, fname)
            if os.path.isfile(path) and fname.endswith('.md'):
                orphan, _ = Category.objects.get_or_create(
                    name='未分类', defaults={'slug': 'uncategorized', 'index': 0})
                n, s = self._import_one_file(path, orphan, admin)
                imported += n
                skipped += s

        total_categories = Category.objects.count()
        total_tags = Tag.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'导入完成: 新增 {imported} 篇, 跳过空文件 {skipped} 个, '
            f'分类树 {total_categories} 个, 标签 {total_tags} 个'))

    def _import_tree(self, dirpath, parent, level, admin):
        """递归将目录树映射为分类树并导入各目录直属文件，
        返回 (分类, 本子树导入篇数, 本子树跳过数)"""
        if level > MAX_LEVEL:
            # 超出层级上限：文件并入当前最深分类
            return None, 0, 0
        index, name = _split_numbered(os.path.basename(dirpath))
        category, _ = self._get_or_create_category(name, parent, index)
        total_imported = total_skipped = 0
        for entry in sorted(os.listdir(dirpath), key=str.lower):
            path = os.path.join(dirpath, entry)
            if os.path.isdir(path):
                _, sub_imported, sub_skipped = self._import_tree(
                    path, category, level + 1, admin)
                total_imported += sub_imported
                total_skipped += sub_skipped
        imported, skipped = self._import_folder_files(dirpath, category, admin)
        return category, total_imported + imported, total_skipped + skipped

    def _get_or_create_category(self, name, parent, index):
        base = name
        for _ in range(MAX_LEVEL):
            existing = Category.objects.filter(
                name__iexact=name, parent_category=parent).first()
            if existing:
                return existing, False
            # Category.name 全局唯一（MySQL 大小写不敏感），
            # 跨父同名时自动加父名作前缀
            clash = Category.objects.filter(name__iexact=name).first()
            if clash and (clash.parent_category_id != (parent.pk if parent else None)):
                name = f'{parent.name}-{base}' if parent else base
                continue
            break
        category = Category.objects.create(
            name=name,
            parent_category=parent,
            index=index)
        # BaseModel.save() 会自动 slugify(name)，中文会被转拼音，
        # 这里显式覆盖为 ASCII 小写或中文原名，保持分类 URL 稳定
        Category.objects.filter(pk=category.pk).update(
            slug=_category_slug(name))
        return category, True

    def _import_folder_files(self, dirpath, category, admin):
        """导入目录内直属的 .md 文件（不递归，子树已由 _import_tree 处理）"""
        imported = skipped = 0
        for fname in sorted(os.listdir(dirpath)):
            path = os.path.join(dirpath, fname)
            if os.path.isfile(path) and fname.endswith('.md'):
                n, s = self._import_one_file(path, category, admin)
                imported += n
                skipped += s
        return imported, skipped

    def _import_one_file(self, path, category, admin):
        with open(path, encoding='utf-8') as f:
            body = f.read()
        if not body.strip():
            return 0, 1
        _, title = _split_numbered(os.path.splitext(os.path.basename(path))[0])
        if not title:
            title = os.path.splitext(os.path.basename(path))[0]
        title = self._unique_title(title, category)
        Article.objects.create(
            title=title,
            body=body,
            status='p',
            type='a',
            comment_status='o',
            pub_time=now(),
            show_toc=True,
            author=admin,
            category=category)
        return 1, 0

    def _unique_title(self, title, category):
        # MySQL utf8mb4 排序规则大小写不敏感，直接用 lower() 判重避免 DB 层冲突
        if title.lower() not in self._title_keys:
            self._title_keys.add(title.lower())
            return title
        # 重名时逐级加父分类前缀，保证唯一
        parents = []
        cur = category
        while cur is not None and len(parents) < MAX_LEVEL:
            parents.append(cur.name)
            cur = cur.parent_category
        prefix = '-'.join(reversed(parents))
        candidate = f'{prefix}-{title}'
        while candidate.lower() in self._title_keys:
            candidate = f'{prefix}-{candidate}'
        self._title_keys.add(candidate.lower())
        return candidate