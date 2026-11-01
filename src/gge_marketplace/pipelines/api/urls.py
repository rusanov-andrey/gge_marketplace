from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import PipelineViewSet

router = SimpleRouter()
router.register(r'pipelines', PipelineViewSet, basename='pipelines')

urlpatterns = [
    path('', include(router.urls)),
]
