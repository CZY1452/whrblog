"""
置顶功能测试
覆盖 is_top 字段默认值、全站列表置顶排序、分类列表不置顶、序列化输出
"""
import tempfile
from pathlib import Path
from datetime import timedelta

from django.utils import timezone
from django.core.management import call_command

from apps.blog.models import Article, Category, Tag
from core.tests.test_base import BaseTestCase


def _ago(days):
    return timezone.now() - timedelta(days=days)


class ArticleTopModelTest(BaseTestCase):
    """Article 模型 is_top 字段"""

    def test_is_top_default_false(self):
        article = self.create_article(title='默认非置顶')
        self.assertFalse(article.is_top)

    def test_is_top_can_be_set_and_persisted(self):
        article = self.create_article(title='置顶文章')
        article.is_top = True
        article.save()
        article.refresh_from_db()
        self.assertTrue(article.is_top)


class ArticleTopApiTest(BaseTestCase):
    """全站文章列表置顶排序"""

    def setUp(self):
        super().setUp()
        # 移除基类自动创建的文章，避免影响排序断言
        self.article.delete()

    def test_list_response_includes_is_top(self):
        self.create_article(title='序列化文章')
        response = self.client.get('/api/articles/')
        results = response.json()['results']
        self.assertIn('is_top', results[0])

    def test_pinned_article_precedes_newer_normal_article(self):
        self.create_article(title='普通新文章', pub_time=timezone.now() + timedelta(days=1))
        pinned = self.create_article(title='置顶旧文章', pub_time=_ago(30))
        pinned.is_top = True
        pinned.save()

        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results[0]['title'], '置顶旧文章')
        self.assertTrue(results[0]['is_top'])

    def test_multiple_pinned_articles_ordered_by_pub_time(self):
        older = self.create_article(title='置顶甲', pub_time=_ago(5))
        newer = self.create_article(title='置顶乙', pub_time=_ago(2))
        older.is_top = True
        older.save()
        newer.is_top = True
        newer.save()

        response = self.client.get('/api/articles/')
        results = response.json()['results']
        top_titles = [r['title'] for r in results if r['is_top']]
        self.assertEqual(top_titles, ['置顶乙', '置顶甲'])

    def test_normal_articles_keep_pub_time_order(self):
        self.create_article(title='旧文章', pub_time=_ago(10))
        self.create_article(title='新文章', pub_time=timezone.now())

        response = self.client.get('/api/articles/')
        results = response.json()['results']
        self.assertEqual(results[0]['title'], '新文章')


class ArticleTopCategoryApiTest(BaseTestCase):
    """分类/标签列表保持原有排序，不做置顶"""

    def setUp(self):
        super().setUp()
        self.article.delete()

    def test_category_list_not_reordered_by_top_flag(self):
        cat = self.create_category(name='分类A')
        self.create_article(title='分类新文', category=cat, pub_time=timezone.now())
        pinned = self.create_article(title='分类置顶旧文', category=cat, pub_time=_ago(10))
        pinned.is_top = True
        pinned.save()

        response = self.client.get(f'/api/articles/?category={cat.slug}')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        # 分类列表不置顶排序，新文章在前
        self.assertEqual(results[0]['title'], '分类新文')
        # 但序列化仍携带 is_top 标识
        by_title = {r['title']: r for r in results}
        self.assertTrue(by_title['分类置顶旧文']['is_top'])


class ArticleImportTreeCommandTest(BaseTestCase):
    """import_knowledge 命令按原目录层级导入分类树"""

    def _build_study_tree(self, root):
        """构造与真实知识库同构的临时目录（4 层）"""
        theme = root / '01-Python'
        sub = theme / '01-基础语法'
        deeper = sub / '01-核心概念'
        deepest = deeper / '嵌套四层'
        for d in (theme, sub, deeper, deepest):
            d.mkdir(parents=True, exist_ok=True)
        (sub / '02-变量与类型.md').write_text('# 变量与类型\n正文', encoding='utf-8')
        (deeper / '03-函数.md').write_text('函数正文', encoding='utf-8')
        (deepest / '04-闭包.md').write_text('闭包正文', encoding='utf-8')
        (theme / '00-python总结.md').write_text('总结', encoding='utf-8')
        (theme / 'READ_ME.md').write_text('', encoding='utf-8')
        return theme

    def test_import_creates_4_level_category_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._build_study_tree(Path(tmp))
            call_command(
                'import_knowledge', tmp,
                '--admin-user', 'admin', '--admin-password', 'x')

            python = Category.objects.get(name='Python', parent_category=None)
            basis = Category.objects.get(name='基础语法', parent_category=python)
            core = Category.objects.get(name='核心概念', parent_category=basis)
            nested = Category.objects.get(name='嵌套四层', parent_category=core)
            # 4 层分类树完整建立
            self.assertEqual(nested.parent_category.parent_category.parent_category, python)
            # 最后一层的文章归入第 4 层分类
            self.assertTrue(Article.objects.filter(title='闭包', category=nested).exists())
            # 中间层文章归入对应子分类
            self.assertTrue(Article.objects.filter(title='变量与类型', category=basis).exists())
            self.assertTrue(Article.objects.filter(title='函数', category=core).exists())
            # 主题目录直属文件归入主题分类
            self.assertTrue(Article.objects.filter(title='python总结', category=python).exists())
            # 标题保留数字前缀之外的名称、空文件跳过
            self.assertEqual(
                Article.objects.exclude(pk=self.article.pk).count(), 4)
            # 分类按目录编号排序
            self.assertEqual(python.index, 1)
            self.assertEqual(basis.index, 1)

    def test_import_same_name_subdirs_get_parent_prefix(self):
        """跨父同名目录自动加父名前缀，避免 Category.name 全局唯一冲突"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            python = root / '01-Python'
            sub_a = python / '01-基础语法'
            frontend = root / '07-前端'
            js = frontend / 'JS'
            sub_b = js / '01-基础语法'
            for d in (python, sub_a, frontend, js, sub_b):
                d.mkdir(parents=True, exist_ok=True)
            (sub_a / '01-变量.md').write_text('变量正文', encoding='utf-8')
            (sub_b / '01-变量.md').write_text('防抖正文', encoding='utf-8')

            call_command(
                'import_knowledge', tmp,
                '--admin-user', 'admin', '--admin-password', 'x')

            # Python 目录下的保持原名，前端 JS 下的自动加 JS 前缀
            python_cat = Category.objects.get(name='Python', parent_category=None)
            basis_py = Category.objects.get(
                name='基础语法', parent_category=python_cat)
            frontend_cat = Category.objects.get(name='前端', parent_category=None)
            js_cat = Category.objects.get(name='JS', parent_category=frontend_cat)
            basis_js = Category.objects.get(
                name='JS-基础语法', parent_category=js_cat)
            # 两篇文章标题都去掉数字前缀且互不冲突
            art_js = Article.objects.get(category=basis_js)
            self.assertNotEqual(art_js.title, '变量')
            self.assertTrue(art_js.title.endswith('变量'))
            self.assertTrue(Article.objects.filter(
                title='变量', category=basis_py).exists())
            self.assertEqual(
                Article.objects.exclude(pk=self.article.pk).count(), 2)

    def test_import_tags_all_descendants_with_theme_tag(self):
        """一级目录设为标签，树内所有层级文章（含子分类）都打标"""
        with tempfile.TemporaryDirectory() as tmp:
            self._build_study_tree(Path(tmp))
            call_command(
                'import_knowledge', tmp,
                '--admin-user', 'admin', '--admin-password', 'x')

            python_tag = Tag.objects.filter(name='Python').first()
            self.assertIsNotNone(python_tag)
            # 4 层最深的文章也被打上主题标签
            for title in ('变量与类型', '函数', '闭包', 'python总结'):
                article = Article.objects.get(title=title)
                self.assertTrue(
                    article.tags.filter(name='Python').exists(),
                    f'文章 {title} 应有 Python 标签')

    def test_add_theme_tags_command_is_idempotent(self):
        """add_theme_tags 命令幂等且只处理根分类树下的文章"""
        with tempfile.TemporaryDirectory() as tmp:
            self._build_study_tree(Path(tmp))
            sub = (Path(tmp) / '01-Python' / '01-基础语法')
            (sub / '10-额外.md').write_text('额外正文', encoding='utf-8')

            call_command(
                'import_knowledge', tmp,
                '--admin-user', 'admin', '--admin-password', 'x')
            # 清掉主题标签后由命令重新补齐
            Tag.objects.filter(name='Python').delete()

            call_command('add_theme_tags')

            articles = Article.objects.exclude(pk=self.article.pk)
            self.assertEqual(articles.count(), 5)
            self.assertEqual(
                set(articles.filter(tags__name='Python')
                    .values_list('title', flat=True)),
                set(articles.values_list('title', flat=True)))

            # 第二次执行仍幂等
            call_command('add_theme_tags')
            self.assertEqual(
                articles.filter(tags__name='Python').count(), 5)