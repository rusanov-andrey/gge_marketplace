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
    @extend_schema(
        summary="Список заказов",
        responses={200: OrderResponseSerializer(many=True)}
    )
    def get(self, request):
        repo = container.order_repository
        orders = repo.get_all()

        serializer = OrderResponseSerializer(orders, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Создание заказа",
        request=OrderCreateSerializer,
        responses={200: OrderResponseSerializer()}
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.create_order_use_case()
        order = use_case.execute(**serializer.validated_data)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)


class OrderDetailAPIView(APIView):
    @extend_schema(
        summary="Информация о заказе",
        responses={200: OrderResponseSerializer()}
    )
    def get(self, request, order_id):
        repo = container.order_repository
        order = repo.get_by_id(order_id)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)

    @extend_schema(
        summary="Удаление заказа",
        responses={200: OrderResponseSerializer()}
    )
    def delete(self, request, order_id):
        use_case = container.delete_order_use_case()
        order = use_case.execute(id=order_id)

        response_serializer = OrderResponseSerializer(order)
        return Response(response_serializer.data)


class OrderItemListAPIView(APIView):
    @extend_schema(
        summary="Информация о позиции заказа",
        responses={200: OrderItemResponseSerializer(many=True)}
    )
    def get(self, request, order_id):
        repo = container.order_repository
        order = repo.get_by_id(order_id)

        serializer = OrderItemResponseSerializer(order.items, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Добавление позиции заказа",
        description="Добавляет товар в заказ. Пересчитывает сумму заказа.",
        request=OrderItemCreateSerializer,
        responses={200: OrderItemResponseSerializer()}
    )
    def post(self, request, order_id):
        serializer = OrderItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.add_item_to_order_use_case()
        item = use_case.execute(order_id=order_id, **serializer.validated_data)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)


class OrderItemDetailAPIView(APIView):
    @extend_schema(
        summary="Информация о позиции заказа",
        responses={200: OrderItemResponseSerializer()}
    )
    def get(self, request, order_id, item_id):
        use_case = container.get_item_from_order_use_case()
        item = use_case.execute(order_id=order_id, item_id=item_id)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)

    @extend_schema(
        summary="Обновление позиции заказа",
        description="Обновляет позицию в заказе. Пересчитывает сумму заказа.",
        request=OrderItemUpdateSerializer,
        responses={200: OrderItemResponseSerializer(many=True)}
    )
    def put(self, request, order_id, item_id):
        serializer = OrderItemUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        use_case = container.update_item_in_order_use_case()
        item = use_case.execute(order_id=order_id, item_id=item_id, **serializer.validated_data)

        response_serializer = OrderItemResponseSerializer(item)
        return Response(response_serializer.data)

    @extend_schema(
        summary="Удаление позиции заказа",
        description="Возвращает агрегированную информацию о количестве проданных единиц и выручке по каждому SKU за указанный период времени.",
        responses={200: OrderItemResponseSerializer()}
    )
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
