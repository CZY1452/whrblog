#!/usr/bin/env python
# encoding: utf-8


import logging
import random
import string
import hashlib
import hmac

import bleach
import markdown
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_sha256(value):
    key = settings.SECRET_KEY.encode('utf-8')
    msg = str(value).encode('utf-8')
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def cache_decorator(expiration=3 * 60):
    def wrapper(func):
        def news(*args, **kwargs):
            try:
                view = args[0]
                key = view.get_cache_key()
            except Exception:
                key = None
            if not key:
                unique_str = repr((func, args, kwargs))

                m = hashlib.sha256(unique_str.encode('utf-8'))
                key = m.hexdigest()
            value = cache.get(key)
            if value is not None:
                if str(value) == '__default_cache_value__':
                    return None
                else:
                    return value
            else:
                logger.debug(
                    'cache_decorator set cache:%s key:%s' %
                    (func.__name__, key))
                value = func(*args, **kwargs)
                if value is None:
                    cache.set(key, '__default_cache_value__', expiration)
                else:
                    cache.set(key, value, expiration)
                return value

        return news

    return wrapper


def expire_view_cache(path, servername, serverport, key_prefix=None):
    '''
    刷新视图缓存
    :param path:url路径
    :param servername:host
    :param serverport:端口
    :param key_prefix:前缀
    :return:是否成功
    '''
    from django.http import HttpRequest
    from django.utils.cache import get_cache_key

    request = HttpRequest()
    request.META = {'SERVER_NAME': servername, 'SERVER_PORT': serverport}
    request.path = path

    key = get_cache_key(request, key_prefix=key_prefix, cache=cache)
    if key:
        logger.info('expire_view_cache:get key:{path}'.format(path=path))
        if cache.get(key):
            cache.delete(key)
        return True
    return False


@cache_decorator()
def get_current_site():
    site = Site.objects.get_current()
    return site


class CommonMarkdown:
    @staticmethod
    def _convert_markdown(value):
        md = markdown.Markdown(
            extensions=[
                'extra',
                'codehilite',
                'toc',
                'tables',
            ]
        )
        body = md.convert(value)
        toc = md.toc
        return body, toc

    @staticmethod
    def get_markdown_with_toc(value):
        body, toc = CommonMarkdown._convert_markdown(value)
        return body, toc

    @staticmethod
    def get_markdown(value):
        body, toc = CommonMarkdown._convert_markdown(value)
        return body


def send_email(emailto, title, content):
    from core.blog_signals import send_email_signal
    send_email_signal.send(
        send_email.__class__,
        emailto=emailto,
        title=title,
        content=content)


def generate_code() -> str:
    """生成随机数验证码"""
    return ''.join(random.sample(string.digits, 6))


def parse_dict_to_url(dict):
    from urllib.parse import quote
    url = '&'.join(['{}={}'.format(quote(k, safe='/'), quote(v, safe='/'))
                    for k, v in dict.items()])
    return url


def get_blog_setting():
    value = cache.get('get_blog_setting')
    if value:
        return value
    else:
        from apps.blog.models import BlogSettings
        if not BlogSettings.objects.count():
            setting = BlogSettings()
            setting.site_name = 'WhrBlog'
            setting.site_description = '记录技术成长，分享 Python/Django 与 Web 开发心得'
            setting.site_seo_description = '专注于 Python、Django 与前后端开发的原创技术博客'
            setting.site_keywords = 'Python, Django, Web 开发, 前端, 个人博客'
            setting.article_sub_length = 300
            setting.sidebar_article_count = 10
            setting.sidebar_comment_count = 5
            setting.show_google_adsense = False
            setting.open_site_comment = True
            setting.analytics_code = ''
            setting.beian_code = ''
            setting.show_gongan_code = False
            setting.comment_need_review = False
            setting.save()
        value = BlogSettings.objects.first()
        logger.info('set cache get_blog_setting')
        cache.set('get_blog_setting', value)
        return value


def delete_sidebar_cache():
    from apps.blog.models import LinkShowType
    keys = ["sidebar" + x for x in LinkShowType.values]
    for k in keys:
        logger.info('delete sidebar key:' + k)
        cache.delete(k)
    # 清理侧边栏聚合视图缓存
    for linktype in ['i', 'l', 'p', 'a', 's']:
        cache.delete(f'sidebar_aggregate_{linktype}')


def delete_view_cache(prefix, keys):
    from django.core.cache.utils import make_template_fragment_key
    key = make_template_fragment_key(prefix, keys)
    cache.delete(key)


# 允许的HTML标签白名单 - 支持markdown常用元素
ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'ul', 'pre', 'strong',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # 标题
    'p', 'span', 'div', 'br', 'hr',  # 段落和分隔
    'table', 'thead', 'tbody', 'tr', 'th', 'td',  # 表格
    'dl', 'dt', 'dd',  # 定义列表
    'img',  # 图片（需配合ALLOWED_ATTRIBUTES限制src）
    'del', 'ins', 'sub', 'sup',  # 文本修饰
]

# 安全的class值白名单 - 只允许代码高亮相关的class
ALLOWED_CLASSES = [
    'codehilite', 'highlight', 'hll', 'c', 'err', 'k', 'l', 'n', 'o', 'p', 'cm', 'cp', 'c1', 'cs',
    'gd', 'ge', 'gr', 'gh', 'gi', 'go', 'gp', 'gs', 'gu', 'gt', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt',
    'ld', 'm', 'mf', 'mh', 'mi', 'mo', 'na', 'nb', 'nc', 'no', 'nd', 'ni', 'ne', 'nf', 'nl', 'nn',
    'nt', 'nv', 'ow', 'w', 'mb', 'mh', 'mi', 'mo', 'sb', 'sc', 'sd', 'se', 'sh', 'si', 'sx', 's2',
    's1', 'ss', 'bp', 'vc', 'vg', 'vi', 'il'
]

def class_filter(tag, name, value):
    """自定义class属性过滤器"""
    if name == 'class':
        # 只允许预定义的安全class值
        allowed_classes = [cls for cls in value.split() if cls in ALLOWED_CLASSES]
        return ' '.join(allowed_classes) if allowed_classes else False
    return value

# 安全的属性白名单
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],  # rel="nofollow" 用于外部链接
    'abbr': ['title'], 
    'acronym': ['title'],
    'img': ['src', 'alt', 'title', 'width', 'height'],  # 图片属性
    'table': ['border', 'cellpadding', 'cellspacing'],
    'th': ['align', 'valign'],
    'td': ['align', 'valign'],
    'span': class_filter,
    'div': class_filter,
    'pre': class_filter,
    'code': class_filter
}

# 安全的协议白名单 - 防止javascript:等危险协议
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def sanitize_html(html):
    """
    安全的HTML清理函数
    使用bleach库进行白名单过滤，防止XSS攻击
    """
    cleaned = bleach.clean(
        html, 
        tags=ALLOWED_TAGS, 
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,  # 限制允许的协议
        strip=True,  # 移除不允许的标签而不是转义
        strip_comments=True  # 移除HTML注释
    )
    
    # 移除空的 style 属性（bleach 有时会保留 style=""）
    import re
    cleaned = re.sub(r'\s*style\s*=\s*["\'][\s]*["\']', '', cleaned)
    
    return cleaned


def strip_markdown(text):
    """剥离常见 Markdown 语法符号与 HTML 标签，得到适合展示的纯文本摘要

    与 core.es_client._clean_text_for_index 逻辑一致，用于生成文章摘要等场景。
    """
    import re
    from django.utils.html import strip_tags
    if not text:
        return ''
    text = strip_tags(text)
    text = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', text)          # 图片
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)        # 链接保留文字
    text = re.sub(r'`{1,3}[^`]*`{1,3}', ' ', text)              # 行内/块级代码
    text = re.sub(r'[#>*_~|]', ' ', text)                       # 标题/引用/加粗/斜体等
    text = re.sub(r'\s+', ' ', text).strip()
    return text
