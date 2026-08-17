from rest_framework import serializers

from apps.accounts.models import BlogUser
from apps.blog.models import Article, BlogSettings, Category, Links, SideBar, Tag


def _blog_setting(context):
    """从序列化上下文取博客设置：同一请求内只查询一次，嵌套序列化复用，消除 N 次 Redis GET"""
    if 'blog_setting' not in context:
        from core.utils import get_blog_setting
        context['blog_setting'] = get_blog_setting()
    return context['blog_setting']


class BlogUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogUser
        fields = ['id', 'username', 'nickname', 'email']
        read_only_fields = ['id', 'username']


class CategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True, default=0)
    url = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()
    child_categories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent_category', 'article_count', 'url', 'seo_title', 'seo_description', 'child_categories']

    def get_url(self, obj):
        return f"/category/{obj.slug}"

    def get_seo_title(self, obj):
        return f"{obj.name} | {_blog_setting(self.context).site_name}"

    def get_seo_description(self, obj):
        count = getattr(obj, 'article_count', 0) or 0
        return f"浏览 {obj.name} 分类下的所有文章，共 {count} 篇文章。"

    def get_child_categories(self, obj):
        from django.db.models import Count, Q
        ctx = self.context
        tree = ctx.get('category_tree')
        if tree is None:
            # 一次性加载全部分类并计算文章数，整棵分类树共享缓存，避免每项一次查询（N+1）
            queryset = Category.objects.annotate(
                article_count=Count('article', filter=Q(article__status='p', article__type='a'))
            )
            tree = {c.id: c for c in queryset}
            ctx['category_tree'] = tree
        children = sorted(
            (c for c in tree.values() if c.parent_category_id == obj.id),
            key=lambda c: -c.index,
        )
        return CategorySerializer(children, many=True, context=ctx).data


class TagSerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(read_only=True, default=0)
    url = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'article_count', 'url', 'seo_title', 'seo_description']

    def get_url(self, obj):
        return f"/tag/{obj.slug}"

    def get_seo_title(self, obj):
        return f"{obj.name} | {_blog_setting(self.context).site_name}"

    def get_seo_description(self, obj):
        count = getattr(obj, 'article_count', 0) or 0
        return f"浏览所有关于 {obj.name} 的文章，共 {count} 篇内容。"


class LinksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Links
        fields = ['id', 'name', 'link', 'sequence', 'is_enable', 'show_type']


class SideBarSerializer(serializers.ModelSerializer):
    class Meta:
        model = SideBar
        fields = ['id', 'name', 'content', 'sequence', 'is_enable']


class BlogSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogSettings
        fields = [
            'id', 'site_name', 'site_description', 'site_seo_description',
            'site_keywords', 'article_sub_length', 'sidebar_article_count',
            'sidebar_comment_count', 'article_comment_count', 'color_scheme',
            'open_site_comment', 'show_google_adsense',
        ]
        read_only_fields = ['id']


class ArticleCreateSerializer(serializers.ModelSerializer):
    """新建文章（管理员，正文为 Markdown 源文本）"""

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'body', 'type', 'status', 'comment_status',
            'show_toc', 'category', 'tags',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        article = Article.objects.create(**validated_data)
        article.tags.set(tags)
        return article

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class ArticleListSerializer(serializers.ModelSerializer):
    author = BlogUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    url = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'url', 'summary', 'type', 'status',
            'views', 'pub_time', 'creation_time', 'author', 'category', 'tags',
        ]
        read_only_fields = fields

    def get_url(self, obj):
        return f"/article/{obj.id}"

    def get_summary(self, obj):
        from core.utils import strip_markdown
        from django.utils.text import Truncator
        length = _blog_setting(self.context).article_sub_length
        plain = strip_markdown(obj.body)
        return Truncator(plain).chars(length, truncate='...')


class ArticleDetailSerializer(ArticleListSerializer):
    body = serializers.SerializerMethodField()
    toc = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    prev_article = serializers.SerializerMethodField()
    next_article = serializers.SerializerMethodField()
    seo_title = serializers.SerializerMethodField()
    seo_description = serializers.SerializerMethodField()
    seo_keywords = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + [
            'body', 'toc', 'comment_status', 'show_toc', 'comment_count',
            'prev_article', 'next_article',
            'seo_title', 'seo_description', 'seo_keywords',
        ]

    def get_body(self, obj):
        from core.utils import CommonMarkdown, sanitize_html
        from core.plugin_manage import hooks
        from core.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
        # 先渲染 Markdown 再清洗（防 XSS），最后交给插件过滤器处理：
        # 插件产物（外部链接 target、图片懒加载属性等）是管理员可信代码，
        # 若再走一遍 bleach 白名单，注入的 target/loading/style 等会被剥掉导致插件失效。
        html = sanitize_html(CommonMarkdown.get_markdown(obj.body))
        context = self.context.get('request')
        article = obj
        return hooks.apply_filters(
            ARTICLE_CONTENT_HOOK_NAME,
            html,
            article=article,
            request=context if context else None,
            context=self.context,
            is_summary=False,
        )

    def get_comment_count(self, obj):
        # 与评论接口保持一致：只统计已启用（审核通过）的评论
        return obj.comment_set.filter(is_enable=True).count()

    def get_toc(self, obj):
        from core.utils import CommonMarkdown
        try:
            _, toc = CommonMarkdown.get_markdown_with_toc(obj.body)
            return toc
        except Exception:
            return ''

    def get_prev_article(self, obj):
        prev = obj.prev_article()
        if not prev:
            return None
        return {'id': prev.id, 'title': prev.title, 'url': f"/article/{prev.id}"}

    def get_next_article(self, obj):
        nxt = obj.next_article()
        if not nxt:
            return None
        return {'id': nxt.id, 'title': nxt.title, 'url': f"/article/{nxt.id}"}

    def get_seo_title(self, obj):
        return f"{obj.title} | {_blog_setting(self.context).site_name}"

    def get_seo_description(self, obj):
        from django.utils.html import strip_tags
        from django.utils.text import Truncator
        from core.utils import CommonMarkdown
        html_content = CommonMarkdown.get_markdown(obj.body)
        description = strip_tags(html_content)
        description = ' '.join(description.split())
        return Truncator(description).chars(150, truncate='...')

    def get_seo_keywords(self, obj):
        tags = [tag.name.strip() for tag in obj.tags.all()]
        return ", ".join(tags) if tags else _blog_setting(self.context).site_keywords
