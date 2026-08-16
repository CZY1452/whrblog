"""Celery 异步任务定义：ES 同步、邮件发送"""
import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task
def sync_article_to_es(article_id):
    """将文章同步到 ES（仅已发布文章）"""
    if getattr(settings, 'TESTING', False):
        return
    try:
        from apps.blog.models import Article
        from core.es_client import index_article
        article = Article.objects.filter(pk=article_id).first()
        if article:
            index_article(article)
    except Exception as e:
        logger.warning('ES sync failed for article %d: %s', article_id, e)


@shared_task
def remove_article_from_es(article_id):
    """从 ES 中移除文章"""
    if getattr(settings, 'TESTING', False):
        return
    try:
        from core.es_client import remove_article
        remove_article(article_id)
    except Exception as e:
        logger.warning('ES remove failed for article %d: %s', article_id, e)


@shared_task
def reindex_articles_for_category(category_id):
    """分类变更时重新索引该分类下的所有文章"""
    if getattr(settings, 'TESTING', False):
        return
    try:
        from apps.blog.models import Article
        from core.es_client import index_article
        articles = Article.objects.filter(
            category_id=category_id, status='p', type='a')
        for article in articles:
            index_article(article)
    except Exception as e:
        logger.warning('ES reindex failed for category %d: %s', category_id, e)


@shared_task
def reindex_articles_for_tag(tag_id):
    """标签变更时重新索引关联的文章"""
    if getattr(settings, 'TESTING', False):
        return
    try:
        from apps.blog.models import Article
        from core.es_client import index_article
        articles = Article.objects.filter(
            tags__id=tag_id, status='p', type='a')
        for article in articles:
            index_article(article)
    except Exception as e:
        logger.warning('ES reindex failed for tag %d: %s', tag_id, e)


@shared_task
def send_comment_email(comment_id):
    """评论/回复通知邮件"""
    if getattr(settings, 'TESTING', False):
        return
    try:
        from apps.comments.models import Comment
        from apps.comments.utils import send_comment_email as _email
        comment = Comment.objects.filter(pk=comment_id).first()
        if comment:
            _email(comment)
    except Exception as e:
        logger.error('评论邮件发送失败: %s', e)


@shared_task
def send_email(emailto, title, content):
    """通用邮件发送（含 EmailSendLog 记录）"""
    if getattr(settings, 'TESTING', False):
        return

    from django.core.mail import EmailMultiAlternatives

    try:
        msg = EmailMultiAlternatives(
            title,
            content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=emailto)
        msg.content_subtype = "html"

        from apps.servermanager.models import EmailSendLog
        log = EmailSendLog()
        log.title = title
        log.content = content
        log.emailto = ','.join(emailto)

        try:
            result = msg.send()
            log.send_result = result > 0
        except Exception as e:
            logger.error(f"失败邮箱号: {emailto}, {e}")
            log.send_result = False
        log.save()
    except Exception as e:
        logger.error('邮件发送任务异常: %s', e)