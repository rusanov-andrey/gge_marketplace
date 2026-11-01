from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('gge_marketplace.catalog.api.urls')),
    path('api/v1/', include('gge_marketplace.orders.api.urls')),
    path('api/v1/', include('gge_marketplace.pipelines.api.urls')),
]
