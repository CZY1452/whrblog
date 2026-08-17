from rest_framework import serializers

from apps.accounts.models import BlogUser
from apps.comments.models import Comment


class CommentAuthorSerializer(serializers.ModelSerializer):
    is_admin = serializers.SerializerMethodField()

    class Meta:
        model = BlogUser
        fields = ['id', 'username', 'nickname', 'is_admin']

    def get_is_admin(self, obj):
        return obj.is_superuser


class CommentSerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(read_only=True)
    parent_id = serializers.IntegerField(
        source='parent_comment_id', required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'body', 'author', 'article', 'parent_id',
            'creation_time', 'is_enable',
        ]
        read_only_fields = ['id', 'author', 'creation_time', 'is_enable']


class CommentDetailSerializer(CommentSerializer):
    reactions = serializers.SerializerMethodField()
    reply_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['reactions', 'reply_count']

    def get_reactions(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if user.is_authenticated:
            return obj.get_reactions_summary(user)
        return obj.get_reactions_summary(None)
