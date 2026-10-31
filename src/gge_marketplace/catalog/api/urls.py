from django.urls import include, path

from .views import ProductDetailAPIView, ProductListAPIView

product_url_patterns = [
    path('products/', ProductListAPIView.as_view(), name='product-list'),
    path('products/<int:product_id>/', ProductDetailAPIView.as_view(), name='product-detail'),
]


urlpatterns = [
    path('catalog/', include(product_url_patterns)),
]
