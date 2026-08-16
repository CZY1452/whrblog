from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .api_views import CommentViewSet

app_name = "comments"

router = SimpleRouter()
router.register(r'comments', CommentViewSet, basename='api-comment')

urlpatterns = [
    path('api/', include(router.urls)),
]
