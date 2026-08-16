from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Article



class Comment(models.Model):
    body = models.TextField('正文', max_length=300)
    creation_time = models.DateTimeField(_('创建时间'), default=now)
    last_modify_time = models.DateTimeField(_('修改时间'), default=now)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('作者'),
        on_delete=models.CASCADE)
    article = models.ForeignKey(
        Article,
        verbose_name=_('文章'),
        on_delete=models.CASCADE)
    parent_comment = models.ForeignKey(
        'self',
        verbose_name=_('父评论'),
        blank=True,
        null=True,
        on_delete=models.CASCADE)
    is_enable = models.BooleanField(_('是否启用'),
                                    default=False, blank=False, null=False)

    class Meta:
        ordering = ['-id']
        verbose_name = _('评论')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
        indexes = [
            # 优化评论列表查询：article + parent_comment + is_enable组合索引
            models.Index(fields=['article', 'parent_comment', 'is_enable'], name='idx_art_parent_enable'),
            # 优化侧边栏评论查询：is_enable + id组合索引
            models.Index(fields=['is_enable', '-id'], name='idx_enable_id'),
        ]

    def __str__(self):
        return self.body

    def get_reactions_summary(self, user=None):
        """
        获取评论的 reactions 统计信息
        返回格式: {
            '👍': {
                'count': 5,
                'has_reacted': True,
                'users': ['Alice', 'Bob', 'Charlie']
            },
            '❤️': {'count': 3, 'has_reacted': False, 'users': [...]},
            ...
        }
        """
        from django.db.models import Count
        from django.db.models import Prefetch

        # 若调用方已 prefetch_related('reactions')（含 select_related('user')），
        # 命中缓存避免列表页 N+1；否则退化为一次 select_related 查询
        prefetch_cache = getattr(self, '_prefetched_objects_cache', None)
        if prefetch_cache and 'reactions' in prefetch_cache:
            all_reactions = list(prefetch_cache['reactions'])
        else:
            all_reactions = list(
                CommentReaction.objects.filter(comment=self)
                .select_related('user')
                .order_by('reaction_type', '-created_at')
            )

        # 在 Python 层分组（数据量小，避免多次数据库查询）
        grouped = {}
        for r in all_reactions:
            if r.reaction_type not in grouped:
                grouped[r.reaction_type] = []
            grouped[r.reaction_type].append(r)

        result = {}
        # 用户已点过的类型：直接从已加载数据判断，避免二次查询
        user_reacted_types = set()
        if user and user.is_authenticated:
            user_reacted_types = set(
                r.reaction_type for r in all_reactions if r.user_id == user.id
            )

        for emoji, reactions in grouped.items():
            user_names = [
                r.user.nickname or r.user.username
                for r in reactions[:10]
            ]
            result[emoji] = {
                'count': len(reactions),
                'has_reacted': emoji in user_reacted_types,
                'users': user_names,
            }

        return result


class CommentReaction(models.Model):
    """
    评论的 Emoji 反应/点赞
    """
    REACTION_CHOICES = [
        ('👍', 'thumbs_up'),
        ('👎', 'thumbs_down'),
        ('❤️', 'heart'),
        ('😄', 'laugh'),
        ('🎉', 'hooray'),
        ('😕', 'confused'),
        ('🚀', 'rocket'),
        ('👀', 'eyes'),
    ]

    comment = models.ForeignKey(
        Comment,
        verbose_name=_('评论'),
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('用户'),
        on_delete=models.CASCADE
    )
    reaction_type = models.CharField(
        _('表情类型'),
        max_length=10,
        choices=REACTION_CHOICES
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)

    class Meta:
        verbose_name = _('评论表情')
        verbose_name_plural = _('评论表情')
        # 每个用户对同一评论的同一种 emoji 只能点一次
        unique_together = ['comment', 'user', 'reaction_type']
        indexes = [
            models.Index(fields=['comment', 'reaction_type'], name='idx_comment_reaction'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.reaction_type} on comment {self.comment.id}'
