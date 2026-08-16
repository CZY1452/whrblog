from django.contrib import admin
from django.contrib.admin.models import DELETION
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse, NoReverseMatch
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


class LogEntryAdmin(admin.ModelAdmin):
    list_filter = [
        'content_type'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display_links = [
        'action_time',
        'get_change_message',
    ]
    list_display = [
        'action_time',
        'user_link',
        'content_type',
        'object_link',
        'get_change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return (
                request.user.is_superuser or
                request.user.has_perm('admin.change_logentry')
        ) and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        content_type = obj.content_type

        if obj.action_flag != DELETION and content_type is not None:
            try:
                url = reverse(
                    'admin:{}_{}_change'.format(content_type.app_label,
                                                content_type.model),
                    args=[obj.object_id]
                )
                return format_html('<a href="{}">{}</a>', url, obj.object_repr)
            except NoReverseMatch:
                pass
        return format_html('{}', obj.object_repr)

    object_link.admin_order_field = 'object_repr'
    object_link.short_description = _('object')

    def user_link(self, obj):
        content_type = ContentType.objects.get_for_model(type(obj.user))
        try:
            url = reverse(
                'admin:{}_{}_change'.format(content_type.app_label,
                                            content_type.model),
                args=[obj.user.pk]
            )
            return format_html('<a href="{}">{}</a>', url, obj.user)
        except NoReverseMatch:
            return format_html('{}', obj.user)

    user_link.admin_order_field = 'user'
    user_link.short_description = _('user')

    def get_queryset(self, request):
        queryset = super(LogEntryAdmin, self).get_queryset(request)
        return queryset.prefetch_related('content_type')

    def get_actions(self, request):
        actions = super(LogEntryAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
