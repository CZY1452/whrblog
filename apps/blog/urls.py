from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .api_views import (
    ArticleCreateAPIView,
    ArticleExportView,
    ArticleImportAPIView,
    ArticleViewSet,
    BlogSettingsViewSet,
    CategoryViewSet,
    CleanCacheAPIView,
    DraftViewSet,
    FileUploadAPIView,
    LinksViewSet,
    SearchViewSet,
    SideBarViewSet,
    SidebarAggregateView,
    SiteInfoView,
    TagViewSet,
)

app_name = "blog"

router = SimpleRouter()
router.register(r'articles', ArticleViewSet, basename='api-article')
router.register(r'categories', CategoryViewSet, basename='api-category')
router.register(r'tags', TagViewSet, basename='api-tag')
router.register(r'links', LinksViewSet, basename='api-link')
router.register(r'sidebars', SideBarViewSet, basename='api-sidebar')
router.register(r'settings', BlogSettingsViewSet, basename='api-settings')
router.register(r'search', SearchViewSet, basename='api-search')
router.register(r'drafts', DraftViewSet, basename='api-draft')

urlpatterns = [
    path('api/articles/export/', ArticleExportView.as_view(), name='api-article-export-batch'),
    path('api/articles/import/', ArticleImportAPIView.as_view(), name='api-article-import'),
    path('api/', include(router.urls)),
    path('api/articles/<int:pk>/export/', ArticleExportView.as_view(), name='api-article-export'),
    path('api/sidebar/', SidebarAggregateView.as_view(), name='api-sidebar-aggregate'),
    path('api/siteinfo/', SiteInfoView.as_view(), name='api-site-info'),
    path('api/upload', FileUploadAPIView.as_view(), name='api-upload'),
    path('api/article_create', ArticleCreateAPIView.as_view(), name='api-article-create'),
    path('api/clean_cache', CleanCacheAPIView.as_view(), name='api-clean-cache'),
    # 兼容旧图床调用端（原 /upload 签名接口）
    path('upload', FileUploadAPIView.as_view(), name='upload'),
]
