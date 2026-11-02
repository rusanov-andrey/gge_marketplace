from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from gge_marketplace.config.container import container
from gge_marketplace.orders.api.serializers import (
    AnalyticsRequestSerializer,
    AnalyticsResponseSerializer,
    OrderCreateSerializer,
    OrderItemCreateSerializer,
    OrderItemResponseSerializer,
    OrderItemUpdateSerializer,
    OrderResponseSerializer,
)


class OrderListAPIView(APIView):
    def get(self, request):
        repo = container.order_repository
        orders = repo.get_all()

        serializer = OrderResponseSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.create_order_use_case()
        order = use_case.execute(**serializer.validated_data)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)


class OrderDetailAPIView(APIView):
    def get(self, request, order_id):
        repo = container.order_repository
        order = repo.get_by_id(order_id)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)

    def delete(self, request, order_id):
        use_case = container.delete_order_use_case()
        order = use_case.execute(id=order_id)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)


class OrderItemListAPIView(APIView):
    def get(self, request, order_id):
        repo = container.order_repository
        order = repo.get_by_id(order_id)

        serializer = OrderItemResponseSerializer(order.items, many=True)
        return Response(serializer.data)

    def post(self, request, order_id):
        serializer = OrderItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.add_item_to_order_use_case()
        item = use_case.execute(order_id=order_id, **serializer.validated_data)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)


class OrderItemDetailAPIView(APIView):
    def get(self, request, order_id, item_id):
        use_case = container.get_item_from_order_use_case()
        item = use_case.execute(order_id=order_id, item_id=item_id)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)

    def put(self, request, order_id, item_id):
        serializer = OrderItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.update_item_in_order_use_case()
        item = use_case.execute(order_id=order_id, item_id=item_id, **serializer.validated_data)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)

    def delete(self, request, order_id, item_id):
        use_case = container.delete_item_from_order_use_case()
        item = use_case.execute(order_id=order_id, item_id=item_id)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)


class OrderAnalyticsAPIView(APIView):

    @extend_schema(
        summary="Аналитика объемов продаж товаров",
        description="Возвращает агрегированную информацию о количестве проданных единиц и выручке по каждому SKU за указанный период времени.",
        request=AnalyticsRequestSerializer,
        responses={200: AnalyticsResponseSerializer(many=True)}
    )
    def post(self, request, *args, **kwargs):
        serializer = AnalyticsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.get_product_sales_analytics_use_case()

        analytics_data = use_case.execute(
            date_from=serializer.validated_data['date_from'],
            date_to=serializer.validated_data['date_to']
        )

        response_serializer = AnalyticsResponseSerializer(analytics_data, many=True)
        return Response(response_serializer.data)
