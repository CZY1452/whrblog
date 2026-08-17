import logging

import django.dispatch
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver

from apps.accounts.models import BlogUser
from apps.blog.models import Article, BlogSettings, Category, Tag
from apps.comments.models import Comment
from core.tasks import (
    reindex_articles_for_category,
    reindex_articles_for_tag,
    remove_article_from_es,
    send_comment_email,
    send_email,
    sync_article_to_es,
)
from core.utils import cache, expire_view_cache, delete_sidebar_cache, delete_view_cache
from core.utils import get_current_site

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 异步任务封装
# ---------------------------------------------------------------------------

def _sync_article_to_es(article):
    """将文章同步到 ES（异步任务，不阻塞请求）"""
    sync_article_to_es.delay(article.id)


def _remove_article_from_es(article_id):
    """从 ES 中移除文章（异步任务）"""
    remove_article_from_es.delay(article_id)


def _reindex_articles_for_category(category_id):
    """分类变更时重新索引该分类下的所有文章（异步任务）"""
    reindex_articles_for_category.delay(category_id)


def _reindex_articles_for_tag(tag_id):
    """标签变更时重新索引关联的文章（异步任务）"""
    reindex_articles_for_tag.delay(tag_id)


send_email_signal = django.dispatch.Signal(
    ['emailto', 'title', 'content'])


@receiver(send_email_signal)
def send_email_signal_handler(sender, **kwargs):
    send_email.delay(
        emailto=kwargs['emailto'],
        title=kwargs['title'],
        content=kwargs['content'])


def _is_views_only_update(update_fields):
    """判断是否仅更新了浏览量字段（此类更新无需清理缓存）"""
    return update_fields == {'views'}


# ---------------------------------------------------------------------------
# post_save 信号按 sender 拆分，避免任意模型保存都触发信号逻辑
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Comment)
def comment_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        return
    if not instance.is_enable:
        return

    # 缓存清理属于副作用，任何异常（如 django_site.domain 未配置导致 DisallowedHost、
    # Redis 不可用等）都不应中断评论的保存
    try:
        path = instance.article.get_absolute_url()
        site = get_current_site().domain
        if site.find(':') > 0:
            site = site[0:site.find(':')]

        expire_view_cache(
            path,
            servername=site,
            serverport=80,
            key_prefix='blogdetail')

        # 清理评论相关缓存
        comment_cache_key = 'article_comments_{id}'.format(
            id=instance.article.id)
        cache.delete(comment_cache_key)
        delete_view_cache('article_comments', [str(instance.article.pk)])
        delete_sidebar_cache()
    except Exception:
        logger.exception('清理评论缓存失败，忽略（不影响评论保存）')

    # 评论/回复通知邮件（异步任务）
    try:
        send_comment_email.delay(instance.id)
    except Exception:
        logger.exception('评论通知邮件入队失败，忽略')


@receiver(post_save, sender=BlogSettings)
@receiver(post_delete, sender=BlogSettings)
def blog_settings_changed(sender, instance, **kwargs):
    """博客设置变更后清理 'get_blog_setting' 缓存，避免修改后最长 10 小时不生效"""
    try:
        cache.delete('get_blog_setting')
    except Exception:
        logger.exception('清理博客设置缓存失败，忽略')


@receiver(post_save, sender=Article)
def article_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        return
    # 浏览量更新不需要清理缓存
    if _is_views_only_update(update_fields):
        return

    try:
        # 清理文章列表首页缓存
        cache.delete('index_1')

        # 清理文章详情缓存
        cache.delete(f'article_comments_{instance.id}')

        # 清理分类相关缓存
        if instance.category:
            category_name = instance.category.name.replace(' ', '_')
            cache.delete(f'category_list_{category_name}_1')

        # 清理标签相关缓存
        try:
            for tag in instance.tags.all():
                cache.delete(f'tag_{tag.name.replace(" ", "_")}_1')
        except Exception:
            pass  # 可能在创建时 tags 还未关联

        # 清理作者相关缓存
        if instance.author:
            from slugify import slugify
            author_slug = slugify(instance.author.username)
            cache.delete(f'author_{author_slug}_1')

        # 清理侧边栏和上下文处理器缓存
        delete_sidebar_cache()
    except Exception:
        logger.exception('清理文章缓存失败，忽略（不影响文章保存）')

    # 同步到 ES（异步任务，Redis 不可用时也不应中断文章保存）
    try:
        _sync_article_to_es(instance)
    except Exception:
        logger.exception('文章同步 ES 入队失败，忽略')


@receiver(post_save, sender=Category)
def category_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        return
    try:
        # 清理分类相关缓存
        cache.delete(f'category_list_{instance.name.replace(" ", "_")}_1')
        delete_sidebar_cache()
    except Exception:
        logger.exception('清理分类缓存失败，忽略')
    # 分类名变更，重新索引该分类下的文章（异步任务）
    try:
        _reindex_articles_for_category(instance.id)
    except Exception:
        logger.exception('分类重索引入队失败，忽略')


@receiver(post_save, sender=Tag)
def tag_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        return
    try:
        # 清理标签相关缓存
        cache.delete(f'tag_{instance.name.replace(" ", "_")}_1')
        delete_sidebar_cache()
    except Exception:
        logger.exception('清理标签缓存失败，忽略')
    # 标签名变更，重新索引关联的文章（异步任务）
    try:
        _reindex_articles_for_tag(instance.id)
    except Exception:
        logger.exception('标签重索引入队失败，忽略')


@receiver(post_save, sender=BlogUser)
def user_post_save(sender, instance, created, raw, using, update_fields, **kwargs):
    if raw:
        return
    # last_login 在登录时更新，user_logged_in 信号已负责清理，这里跳过避免重复
    if update_fields and set(update_fields) <= {'last_login'}:
        return
    try:
        delete_sidebar_cache()
    except Exception:
        logger.exception('清理用户缓存失败，忽略')


@receiver(user_logged_in)
@receiver(user_logged_out)
def user_auth_callback(sender, request, user, **kwargs):
    if user and user.username:
        logger.info(user)
        delete_sidebar_cache()


@receiver(post_delete, sender=Article)
def model_post_delete_callback(sender, instance, **kwargs):
    """文章删除后从 ES 中移除对应文档"""
    try:
        _remove_article_from_es(instance.id)
    except Exception:
        logger.exception('文章移除 ES 入队失败，忽略')


@receiver(m2m_changed, sender=Article.tags.through)
def article_tags_changed(sender, instance, action, **kwargs):
    """文章标签变更时重新索引文章"""
    if action in ('post_add', 'post_remove', 'post_clear'):
        try:
            _sync_article_to_es(instance)
        except Exception:
            logger.exception('文章标签变更重索引入队失败，忽略')
