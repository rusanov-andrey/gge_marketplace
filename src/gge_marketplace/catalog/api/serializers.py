from rest_framework import serializers

from gge_marketplace.common.api.serializers import TimeStampedSerializer


class ProductCreateSerializer(serializers.Serializer):
    stock_keeping_unit = serializers.CharField(max_length=64, required=True, allow_null=False, allow_blank=False)
    title = serializers.CharField(max_length=255, required=True, allow_null=False, allow_blank=False)
    description = serializers.CharField(max_length=1024, required=True, allow_null=False, allow_blank=False)
    price = serializers.FloatField(min_value=0, required=True)


class ProductUpdateSerializer(ProductCreateSerializer):
    pass


class ProductResponseSerializer(TimeStampedSerializer):
    id = serializers.IntegerField()
    stock_keeping_unit = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    price = serializers.FloatField()
