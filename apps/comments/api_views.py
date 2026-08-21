from django.db.models import Count, Prefetch, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blog.models import Article
from apps.comments.models import Comment, CommentReaction
from apps.comments.serializers import (
    CommentDetailSerializer,
    CommentSerializer,
)


class CommentViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     mixins.CreateModelMixin,
                     viewsets.GenericViewSet):
    """评论列表、详情与提交"""
    queryset = Comment.objects.select_related('author', 'article')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'list':
            return CommentDetailSerializer
        return CommentSerializer

    def get_queryset(self):
        qs = super().get_queryset().filter(is_enable=True)
        # 一次性统计每条评论的启用回复数，避免序列化时逐条查询造成 N+1
        # 注意：parent_comment 未设 related_name，查询字符串用 related_query_name='comment'
        # （accessor 名才是 comment_set，二者不同，混用会抛 FieldError）
        qs = qs.annotate(
            reply_count=Count('comment', filter=Q(comment__is_enable=True))
        )
        # 显式排序：annotate 会破坏 Meta.ordering，导致分页结果不稳定（UnorderedObjectListWarning）
        qs = qs.order_by('-id')
        # 批量预取 reactions + user，避免列表页 get_reactions_summary 逐条查询（N+1）
        qs = qs.prefetch_related(
            Prefetch(
                'reactions',
                queryset=CommentReaction.objects.select_related('user')
                .order_by('reaction_type', '-created_at'),
            )
        )
        article_id = self.request.query_params.get('article')
        if article_id:
            qs = qs.filter(article_id=article_id)
        parent_id = self.request.query_params.get('parent')
        if parent_id:
            qs = qs.filter(parent_comment_id=parent_id)
        return qs

    def create(self, request, *args, **kwargs):
        article_id = request.data.get('article') or request.data.get('article_id')
        body = (request.data.get('body') or request.data.get('content') or '').strip()
        if not body:
            return Response({'error': '评论内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if len(body) > 300:
            return Response({'error': '评论内容不能超过 300 字'}, status=status.HTTP_400_BAD_REQUEST)

        article = Article.objects.filter(pk=article_id).first()
        if not article:
            return Response({'error': '文章未找到'}, status=status.HTTP_404_NOT_FOUND)
        # 评论关闭，或文章未发布（草稿/页面）时禁止评论
        if article.comment_status == 'c' or article.status != 'p' or article.type != 'a':
            return Response({'error': '该文章评论已关闭'}, status=status.HTTP_400_BAD_REQUEST)

        from core.utils import get_blog_setting
        settings = get_blog_setting()

        parent_id = request.data.get('parent_id')
        parent_comment = None
        if parent_id:
            parent_comment = Comment.objects.filter(pk=parent_id).first()
            if not parent_comment:
                return Response({'error': '未找到父评论'},
                                status=status.HTTP_400_BAD_REQUEST)
            # 父评论必须属于同一篇文章，防止跨文章回复
            if parent_comment.article_id != article.id:
                return Response({'error': '无效的父评论。'},
                                status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            body=body,
            author=request.user,
            article=article,
            parent_comment=parent_comment,
            is_enable=not settings.comment_need_review,
        )
        serializer = CommentDetailSerializer(
            comment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'])
    def react(self, request, pk=None):
        """评论 Emoji 反应：GET 查看，POST 切换"""
        comment = self.get_object()

        if request.method == 'GET':
            return Response({
                'success': True,
                'reactions': comment.get_reactions_summary(request.user if request.user.is_authenticated else None),
            })

        reaction_type = request.data.get('reaction_type')
        valid_reactions = [choice[0] for choice in CommentReaction.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return Response({'error': '无效的反应类型。'},
                            status=status.HTTP_400_BAD_REQUEST)

        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type,
        )
        action_ = 'added' if created else 'removed'
        if not created:
            reaction.delete()

        return Response({
            'success': True,
            'action': action_,
            'reactions': comment.get_reactions_summary(request.user),
        })
