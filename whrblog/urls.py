"""WhrBlog URL 配置

纯 API 架构：所有业务数据由 DRF 接口提供，前端为独立托管的 Vue SPA。
仅保留：API、admin、sitemap、健康检查、静态资源。
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.http import JsonResponse
from django.urls import include, path, re_path
import time

from core.admin_site import admin_site
from core.sitemap import ArticleSiteMap, CategorySiteMap, StaticViewSitemap, TagSiteMap, UserSiteMap

sitemaps = {
    'blog': ArticleSiteMap,
    'Category': CategorySiteMap,
    'Tag': TagSiteMap,
    'User': UserSiteMap,
    'static': StaticViewSitemap
}

handler404 = 'core.error_views.page_not_found_view'
handler500 = 'core.error_views.server_error_view'
handler403 = 'core.error_views.permission_denied_view'


def health_check(request):
    """健康检查接口"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': time.time()
    })


urlpatterns = [
    path('health/', health_check, name='health_check'),
    re_path(r'^admin/', admin_site.urls),
    re_path(r'', include('apps.blog.urls', namespace='blog')),
    re_path(r'', include('apps.comments.urls', namespace='comment')),
    re_path(r'', include('apps.accounts.urls', namespace='account')),
    re_path(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
            name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
