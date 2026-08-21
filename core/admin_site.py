from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

from apps.accounts.admin import *
from apps.blog.admin import *
from apps.blog.models import *
from apps.comments.admin import *
from apps.comments.models import *
from core.logentryadmin import LogEntryAdmin


class WhrBlogAdminSite(AdminSite):
    site_header = 'whrblog administration'
    site_title = 'whrblog site admin'

    def __init__(self, name='admin'):
        super().__init__(name)

    def has_permission(self, request):
        return request.user.is_superuser


admin_site = WhrBlogAdminSite(name='admin')

admin_site.register(Article, ArticleAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Links, LinksAdmin)
admin_site.register(SideBar, SideBarAdmin)
admin_site.register(BlogSettings, BlogSettingsAdmin)

admin_site.register(BlogUser, BlogUserAdmin)

admin_site.register(Comment, CommentAdmin)

admin_site.register(Site, SiteAdmin)

admin_site.register(LogEntry, LogEntryAdmin)
