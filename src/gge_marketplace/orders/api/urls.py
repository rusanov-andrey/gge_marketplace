from django.urls import path

from .views import (
    OrderAnalyticsAPIView,
    OrderDetailAPIView,
    OrderItemDetailAPIView,
    OrderItemListAPIView,
    OrderListAPIView,
)

urlpatterns = [
    path('orders/', OrderListAPIView.as_view(), name='order-list'),
    path('orders/<int:order_id>/', OrderDetailAPIView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/items/', OrderItemListAPIView.as_view(), name='order-item-list'),
    path('orders/<int:order_id>/items/<int:item_id>/', OrderItemDetailAPIView.as_view(), name='order-item-detail'),
    path('orders/analytics', OrderAnalyticsAPIView.as_view(), name='orders-analytics'),
]
