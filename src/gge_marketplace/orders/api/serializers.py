from rest_framework import serializers

from gge_marketplace.common.api.serializers import TimeStampedSerializer


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price_on_buy = serializers.FloatField(min_value=0)


class OrderItemUpdateSerializer(OrderItemCreateSerializer):
    pass


class OrderItemResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price_on_buy = serializers.FloatField()


class OrderCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()


class OrderResponseSerializer(TimeStampedSerializer):
    id = serializers.IntegerField()
    user_id = serializers.IntegerField()
    total_price = serializers.FloatField()
    items = OrderItemResponseSerializer(many=True)


class AnalyticsRequestSerializer(serializers.Serializer):
    date_from = serializers.DateField(format="%Y-%m-%d", help_text="Формат: YYYY-MM-DD")
    date_to = serializers.DateField(format="%Y-%m-%d", help_text="Формат: YYYY-MM-DD")


class AnalyticsResponseSerializer(serializers.Serializer):
    product_stock_keeping_unit = serializers.CharField()
    product_title = serializers.CharField()
    total_quantity = serializers.IntegerField()
    total_revenue = serializers.FloatField()
