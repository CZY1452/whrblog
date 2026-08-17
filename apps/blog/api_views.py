import logging

from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

from apps.blog.models import Article, BlogSettings, Category, Links, SideBar, Tag
from apps.blog.serializers import (
    ArticleCreateSerializer,
    ArticleDetailSerializer,
    ArticleListSerializer,
    BlogSettingsSerializer,
    CategorySerializer,
    LinksSerializer,
    SideBarSerializer,
    TagSerializer,
)


class ArticleViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """文章列表与详情"""
    queryset = Article.objects.select_related(
        'author', 'category').prefetch_related('tags').filter(
        type='a', status='p')
    serializer_class = ArticleListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        tag = self.request.query_params.get('tag')
        author = self.request.query_params.get('author')
        if category:
            qs = qs.filter(category__slug=category)
        if tag:
            qs = qs.filter(tags__slug=tag)
        if author:
            qs = qs.filter(author__username=author)
        return qs

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 阅读量 +1：同一 IP 对同一文章 10 分钟内只计一次，降低高流量下的热点写；
        # Redis 不可用时降级为直接计数
        from django.core.cache import cache
        key = f"article_view_{request.META.get('REMOTE_ADDR', 'unknown')}_{instance.id}"
        try:
            counted = cache.get(key)
        except Exception:
            counted = None
        if not counted:
            instance.viewed()
            try:
                cache.set(key, '1', 600)
            except Exception:
                pass
        serializer = ArticleDetailSerializer(instance, context={'request': request})
        return Response(serializer.data)


class ArticleCreateAPIView(APIView):
    """新建文章（仅管理员）"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ArticleCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(author=request.user)
        output = ArticleDetailSerializer(
            serializer.instance, context={'request': request})
        return Response(output.data, status=201)


class DraftViewSet(mixins.ListModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   viewsets.GenericViewSet):
    """草稿箱：管理员查看、编辑、删除、发布草稿"""
    serializer_class = ArticleListSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Article.objects.select_related(
            'author', 'category'
        ).prefetch_related('tags').filter(
            type='a', status='d'
        ).order_by('-last_modify_time')

    def get_serializer_class(self):
        if self.action in ('partial_update', 'update'):
            return ArticleCreateSerializer
        if self.action == 'retrieve':
            return ArticleCreateSerializer
        return ArticleListSerializer

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """将草稿发布为正式文章"""
        article = self.get_object()
        article.status = 'p'
        article.save(update_fields=['status', 'last_modify_time'])
        output = ArticleDetailSerializer(article, context={'request': request})
        return Response(output.data)


class CategoryViewSet(mixins.ListModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    """分类列表与详情"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        from django.db.models import Count, Q
        return Category.objects.annotate(
            article_count=Count('article', filter=Q(article__status='p', article__type='a'))
        )


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """标签列表与详情"""
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        from django.db.models import Count, Q
        return Tag.objects.annotate(
            article_count=Count('article', filter=Q(article__status='p', article__type='a'))
        )


class LinksViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """友情链接"""
    queryset = Links.objects.filter(is_enable=True)
    serializer_class = LinksSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class SideBarViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """侧边栏"""
    queryset = SideBar.objects.filter(is_enable=True)
    serializer_class = SideBarSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class BlogSettingsViewSet(viewsets.GenericViewSet):
    """博客设置（只读）"""
    serializer_class = BlogSettingsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request, *args, **kwargs):
        instance = BlogSettings.objects.first()
        if not instance:
            return Response({'detail': 'No blog settings found'}, status=404)
        return Response(self.get_serializer(instance).data)


class SearchViewSet(viewsets.ViewSet):
    """搜索文章（优先使用 Elasticsearch，不可用时回退到 ORM 模糊查询）"""
    permission_classes = [IsAuthenticatedOrReadOnly]
    max_page_size = 50

    def _pagination_params(self, request):
        """解析并约束分页参数"""
        try:
            page = max(1, int(request.query_params.get('page', 1)))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = int(request.query_params.get('page_size', 20))
        except (TypeError, ValueError):
            page_size = 20
        page_size = max(1, min(page_size, self.max_page_size))
        return page, page_size

    def list(self, request):
        query = request.query_params.get('q', '').strip()
        page, page_size = self._pagination_params(request)
        if not query:
            return Response({'query': '', 'total': 0, 'results': []})

        # 优先使用 ES 全文检索（测试时跳过，因为 TESTING 模式下不索引）
        if not getattr(settings, 'TESTING', False):
            try:
                from core.es_client import search_articles, is_available
                if is_available():
                    es_result = search_articles(query, page=page, page_size=page_size)
                    results = self._es_results_to_articles(es_result['results'])
                    return Response({
                        'query': query,
                        'total': es_result['total'],
                        'page': page,
                        'page_size': page_size,
                        'results': results,
                    })
            except Exception as exc:
                # ES 出错时记录日志再回退到 ORM，避免静默吞掉异常
                logger.warning('ES 搜索失败，回退到 ORM 查询：%s', exc)

        # 回退到 ORM 模糊查询（搜索标题和正文）
        from django.core.paginator import Paginator
        from django.db.models import Q
        queryset = Article.objects.filter(
            type='a', status='p'
        ).filter(
            Q(title__icontains=query) | Q(body__icontains=query)
        ).select_related('author', 'category').prefetch_related('tags')

        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        serializer = ArticleListSerializer(
            page_obj.object_list, many=True, context={'request': request})
        return Response({
            'query': query,
            'total': paginator.count,
            'page': page,
            'page_size': page_size,
            'results': serializer.data,
        })

    def _es_results_to_articles(self, es_results):
        """将 ES 搜索结果转为前端兼容的文章列表格式（保持 ES 相关性排序）"""
        if not es_results:
            return []
        # 建立 id -> ES 条目 的映射，用于附加 highlight/score
        es_by_id = {r['id']: r for r in es_results if 'id' in r}
        ids = list(es_by_id.keys())
        if not ids:
            return []

        articles = {a.id: a for a in Article.objects.filter(
            id__in=ids
        ).select_related('author', 'category').prefetch_related('tags')}

        # 按 ES 返回顺序组装文章对象，跳过已不存在于数据库的脏数据
        ordered = [articles[i] for i in ids if i in articles]
        # 一次性批量序列化（many=True），避免逐条实例化 serializer
        serialized = ArticleListSerializer(ordered, many=True).data

        result = []
        for item in serialized:
            es_item = es_by_id.get(item['id'], {})
            if 'highlight' in es_item:
                item['highlight'] = es_item['highlight']
            item['score'] = es_item.get('score', 0)
            result.append(item)
        return result


def _render_sidebar_markdown(content):
    """将侧边栏公告内容的 markdown 渲染并清洗为 HTML（复用 sidebar_markdown 过滤逻辑）"""
    from core.utils import CommonMarkdown, sanitize_html
    return sanitize_html(CommonMarkdown.get_markdown(content))


class SidebarAggregateView(APIView):
    """侧边栏聚合数据（替代模板的 load_sidebar 标签）"""
    permission_classes = [AllowAny]
    linktype_param = 'linktype'

    def get(self, request):
        from django.db.models import Count, Q
        from django.core.cache import cache
        from core.utils import get_blog_setting
        from apps.blog.models import LinkShowType

        linktype = request.query_params.get(self.linktype_param, 'p')
        # 校验 linktype 白名单，防止非法值污染缓存键空间
        if linktype not in LinkShowType.values:
            linktype = 'p'
        cache_key = f'sidebar_aggregate_{linktype}'
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)

        blogsetting = get_blog_setting()

        recent_articles = Article.objects.filter(
            status='p'
        ).select_related('author', 'category')[:blogsetting.sidebar_article_count]

        sidebar_categorys = Category.objects.annotate(
            article_count=Count('article', filter=Q(article__status='p', article__type='a'))
        )

        extra_sidebars = SideBar.objects.filter(
            is_enable=True
        ).order_by('sequence')

        most_read_articles = Article.objects.filter(
            status='p'
        ).select_related('author', 'category').order_by(
            '-views'
        )[:blogsetting.sidebar_article_count]

        links = Links.objects.filter(is_enable=True).filter(
            Q(show_type=str(linktype)) | Q(show_type=LinkShowType.A)
        )

        # 标签云 — 按文章数排序，取 top 20，size = (count/avg)*5+10
        increment = 5
        article_id = request.query_params.get('article_id')
        if article_id:
            article = Article.objects.filter(id=article_id, status='p').first()
            tag_objs = list(article.tags.all()) if article else []
        else:
            tag_objs = list(Tag.objects.annotate(
                article_count=Count('article', filter=Q(article__status='p', article__type='a'))
            ))
        sidebar_tags = []
        if tag_objs:
            s = sorted(
                [t for t in [(t, getattr(t, 'article_count', 0) or t.get_article_count()) for t in tag_objs] if t[1]],
                key=lambda x: x[1], reverse=True
            )[:20]
            count = sum([t[1] for t in s])
            dd = 1 if (count == 0 or not len(s)) else count / len(s)
            sidebar_tags = [
                {
                    'id': t[0].id,
                    'name': t[0].name,
                    'slug': t[0].slug,
                    'count': t[1],
                    'size': (t[1] / dd) * increment + 10,
                    'url': f"/tag/{t[0].slug}",
                }
                for t in s
            ]

        article_ctx = {
            'recent_articles': ArticleListSerializer(
                recent_articles, many=True, context={'request': request}).data,
            'most_read_articles': ArticleListSerializer(
                most_read_articles, many=True, context={'request': request}).data,
        }

        result = {
            'recent_articles': article_ctx['recent_articles'],
            'most_read_articles': article_ctx['most_read_articles'],
            'sidebar_categorys': CategorySerializer(
                sidebar_categorys, many=True, context={'request': request}).data,
            'links': LinksSerializer(
                links, many=True, context={'request': request}).data,
            'sidebar_tags': sidebar_tags,
            'extra_sidebars': [
                {
                    'id': sb.id,
                    'name': sb.name,
                    'content_html': _render_sidebar_markdown(sb.content),
                    'sequence': sb.sequence,
                }
                for sb in extra_sidebars
            ],
            'show_google_adsense': blogsetting.show_google_adsense,
            'google_adsense_codes': blogsetting.google_adsense_codes,
            'open_site_comment': blogsetting.open_site_comment,
            'show_gongan_code': blogsetting.show_gongan_code,
        }
        cache.set(cache_key, result, 300)  # 缓存 5 分钟
        return Response(result)


class FileUploadAPIView(APIView):
    """图床上传（原 blog.views.fileupload，供后台编辑器等调用方使用）

    仅管理员可上传（图床用于后台编辑器，避免任意注册用户滥用存储/上传）。
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        import os
        import uuid
        from django.conf import settings as django_settings
        from django.utils import timezone

        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

        response = []
        for filename in request.FILES:
            uploaded = request.FILES[filename]

            # 文件大小校验
            if uploaded.size > MAX_FILE_SIZE:
                return Response({'error': f'文件过大，最大允许 {MAX_FILE_SIZE // (1024*1024)}MB'}, status=400)

            ext = os.path.splitext(filename)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                return Response({'error': f'不支持的文件格式: {ext}'}, status=400)

            # 保存到 MEDIA_ROOT（而非 static），避免 collectstatic 混入上传文件、
            # 也避免 ManifestStaticFilesStorage 对上传文件做哈希重命名
            timestr = timezone.now().strftime('%Y/%m/%d')
            rel_dir = os.path.join('image', timestr)
            base_dir = os.path.join(django_settings.MEDIA_ROOT, rel_dir)
            os.makedirs(base_dir, exist_ok=True)

            fname = f'{uuid.uuid4().hex}{ext}'
            savepath = os.path.normpath(os.path.join(base_dir, fname))
            if not savepath.startswith(base_dir):
                return Response({'error': '非法路径'}, status=400)
            with open(savepath, 'wb+') as wfile:
                for chunk in uploaded.chunks():
                    wfile.write(chunk)

            # 验证并压缩图片（白名单内均为图片格式）
            try:
                from PIL import Image
                image = Image.open(savepath)
                image.verify()  # 验证是否为合法图片
                image = Image.open(savepath)
                image.save(savepath, quality=85, optimize=True)
            except Exception:
                os.remove(savepath)
                return Response({'error': '无效的图片文件'}, status=400)

            # 返回基于 MEDIA_URL 的可访问 URL（前端由 Nginx /media/ 直接代理）
            rel_path = os.path.join(rel_dir, fname).replace(os.sep, '/')
            url = django_settings.MEDIA_URL.rstrip('/') + '/' + rel_path
            response.append(url)
        return Response(response)


class CleanCacheAPIView(APIView):
    """清理缓存（仅超管）"""
    permission_classes = [IsAdminUser]

    def post(self, request):
        from django.core.cache import cache
        cache.clear()
        return Response({'success': True, 'message': '缓存已清理'})


class SiteInfoView(APIView):
    """站点全局信息（替代 context processor 注入的 SITE_* / nav_category_list / nav_pages）"""
    permission_classes = [AllowAny]

    def get(self, request):
        import datetime
        from django.db.models import Count, Q
        from core.utils import get_blog_setting
        setting = get_blog_setting()

        # 一次查询获取所有分类及其「直接」文章数（仅统计已发布文章，排除"页面"类型）
        all_categories = Category.objects.annotate(
            direct_count=Count('article', filter=Q(article__status='p', article__type='a'))
        )
        # 构建父-子映射，避免嵌套查询
        children_map = {}
        for c in all_categories:
            pid = c.parent_category_id
            if pid:
                children_map.setdefault(pid, []).append(c)

        # 计算每个分类的「总篇数」（直接文章 + 所有子孙分类文章），供导航栏展示
        _total_cache = {}

        def _total_count(c):
            if c.id in _total_cache:
                return _total_cache[c.id]
            total = c.direct_count or 0
            for child in children_map.get(c.id, []):
                total += _total_count(child)
            _total_cache[c.id] = total
            return total

        nav_category_list = [
            {
                'id': c.id,
                'name': c.name,
                'slug': c.slug,
                'url': c.get_absolute_url(),
                'parent_category': c.parent_category_id,
                'article_count': _total_count(c),
                'child_categories': [
                    {
                        'id': sub.id,
                        'name': sub.name,
                        'slug': sub.slug,
                        'url': sub.get_absolute_url(),
                        'article_count': _total_count(sub),
                    }
                    for sub in children_map.get(c.id, [])
                ],
            }
            for c in all_categories if c.parent_category_id is None
        ]

        # 标签及其文章数（仅统计已发布文章，按篇数降序、同名升序）
        nav_tags = [
            {
                'id': t.id,
                'name': t.name,
                'slug': t.slug,
                'url': t.get_absolute_url(),
                'article_count': t.article_count,
            }
            for t in Tag.objects.annotate(
                article_count=Count('article', filter=Q(article__status='p', article__type='a'))
            ).order_by('-article_count', 'name')
        ]

        nav_pages = Article.objects.filter(
            type='p', status='p').order_by('pub_time')

        return Response({
            'SITE_NAME': setting.site_name,
            'SITE_DESCRIPTION': setting.site_description,
            'SITE_SEO_DESCRIPTION': setting.site_seo_description,
            'SITE_KEYWORDS': setting.site_keywords,
            'SITE_BASE_URL': request.build_absolute_uri('/'),
            'CURRENT_YEAR': datetime.date.today().year,
            'BEIAN_CODE': setting.beian_code,
            'BEIAN_CODE_GONGAN': setting.gongan_beiancode,
            'SHOW_GONGAN_CODE': setting.show_gongan_code,
            'ANALYTICS_CODE': setting.analytics_code,
            'GLOBAL_HEADER': setting.global_header,
            'GLOBAL_FOOTER': setting.global_footer,
            'COLOR_SCHEME': setting.color_scheme,
            'OPEN_SITE_COMMENT': setting.open_site_comment,
            'SHOW_GOOGLE_ADSENSE': setting.show_google_adsense,
            'GOOGLE_ADSENSE_CODES': setting.google_adsense_codes,
            'COMMENT_NEED_REVIEW': setting.comment_need_review,
            'ARTICLE_SUB_LENGTH': setting.article_sub_length,
            'nav_category_list': nav_category_list,
            'nav_tags': nav_tags,
            'nav_pages': [
                {
                    'id': p.id,
                    'title': p.title,
                    'url': p.get_absolute_url(),
                }
                for p in nav_pages
            ],
        })


def _quote_yaml(value):
    """将值安全包进 YAML 双引号字符串：转义反斜杠/双引号，压缩换行防注入"""
    return str(value).replace('\\', '\\\\').replace('"', '\\"') \
        .replace('\r', ' ').replace('\n', ' ')


def _safe_filename(name):
    """将标题转为安全的文件名：替换路径分隔符等非法字符"""
    import re
    return re.sub(r'[\\/:*?"<>|\r\n]', '_', name)


def _article_to_markdown(article):
    """将文章实例转换为带 YAML front matter 的 Markdown 字符串"""
    tags = [t.name for t in article.tags.all()]
    pub_time = article.pub_time.strftime('%Y-%m-%d %H:%M') if article.pub_time else ''

    lines = [
        '---',
        f'title: "{_quote_yaml(article.title)}"',
        f'date: "{_quote_yaml(pub_time)}"',
        f'category: "{_quote_yaml(article.category.name)}"',
        f'tags: [{", ".join(_quote_yaml(t) for t in tags)}]',
        '---',
        '',
        f'# {article.title}',
        '',
        article.body or '',
    ]
    return '\n'.join(lines)


class ArticleExportView(APIView):
    """文章 Markdown 导出

    单篇：GET /api/articles/<id>/export/  → 下载 .md 文件
    批量：GET /api/articles/export/?ids=1,2,3  → 下载 .zip 文件
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk=None):
        if pk:
            return self._export_single(pk)
        ids_str = request.query_params.get('ids', '')
        if not ids_str:
            return Response({'detail': '请提供文章 id 或 ids 参数'}, status=400)
        return self._export_batch(ids_str)

    def _export_single(self, pk):
        from django.http import HttpResponse
        from urllib.parse import quote
        # 仅允许导出已发布文章，防止匿名用户通过接口导出草稿内容（越权/信息泄露）
        article = Article.objects.filter(
            pk=pk, status='p', type='a'
        ).prefetch_related('tags', 'category').first()
        if not article:
            return Response({'detail': '文章不存在'}, status=404)
        md = _article_to_markdown(article)
        encoded_name = quote(f'{article.title}.md')
        response = HttpResponse(md.encode('utf-8'), content_type='text/markdown; charset=utf-8')
        response['Content-Disposition'] = f"attachment; filename*=UTF-8''{encoded_name}"
        return response

    def _export_batch(self, ids_str):
        import io
        import zipfile
        from django.http import HttpResponse

        try:
            ids = [int(i) for i in ids_str.split(',') if i.strip()]
        except ValueError:
            return Response({'detail': 'ids 参数格式错误'}, status=400)

        if not ids:
            return Response({'detail': '请提供至少一个文章 id'}, status=400)

        articles = Article.objects.filter(
            pk__in=ids, status='p', type='a'
        ).prefetch_related('tags', 'category')

        if not articles.exists():
            return Response({'detail': '未找到可导出的文章'}, status=404)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for article in articles:
                md = _article_to_markdown(article)
                zf.writestr(f'{_safe_filename(article.title)}.md', md.encode('utf-8'))

        buf.seek(0)
        response = HttpResponse(buf.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="articles.zip"'
        return response


def _parse_markdown_file(content, filename=''):
    """解析 Markdown 文件内容，提取 front matter 元数据和正文

    返回: {'title': str, 'category': str, 'tags': list, 'date': str, 'body': str}
    """
    import re
    import yaml

    result = {'title': '', 'category': '', 'tags': [], 'date': '', 'body': content}

    # 尝试解析 YAML front matter
    fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', content, re.DOTALL)
    if fm_match:
        try:
            meta = yaml.safe_load(fm_match.group(1)) or {}
            result['title'] = str(meta.get('title', ''))
            result['category'] = str(meta.get('category', ''))
            result['date'] = str(meta.get('date', ''))
            tags = meta.get('tags', [])
            if isinstance(tags, list):
                result['tags'] = [str(t) for t in tags if t]
            elif isinstance(tags, str) and tags:
                result['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
            result['body'] = fm_match.group(2)
        except yaml.YAMLError:
            pass  # front matter 解析失败，当作纯文本处理

    # 如果没有从 front matter 获取到标题，尝试从第一个 # 标题提取
    if not result['title']:
        heading_match = re.search(r'^#\s+(.+)$', result['body'], re.MULTILINE)
        if heading_match:
            result['title'] = heading_match.group(1).strip()
        elif filename:
            # 从文件名推断标题（去掉 .md 后缀）
            name = re.sub(r'\.md$', '', filename, flags=re.IGNORECASE)
            result['title'] = name

    return result


class ArticleImportAPIView(APIView):
    """文章 Markdown 导入

    POST /api/articles/import/  上传 .md 文件，解析返回结构化数据供前端填充表单
    支持带 YAML front matter 的 .md 和纯 Markdown 文件
    """
    permission_classes = [IsAdminUser]

    def post(self, request):
        uploaded = request.FILES.get('file')
        if not uploaded:
            return Response({'detail': '请上传 .md 文件'}, status=400)

        filename = uploaded.name or ''
        if not filename.lower().endswith('.md'):
            return Response({'detail': '仅支持 .md 格式文件'}, status=400)

        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        if uploaded.size > MAX_SIZE:
            return Response({'detail': '文件大小不能超过 10MB'}, status=400)

        try:
            content = uploaded.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response({'detail': '文件编码错误，请使用 UTF-8 编码'}, status=400)

        parsed = _parse_markdown_file(content, filename)
        return Response(parsed)
