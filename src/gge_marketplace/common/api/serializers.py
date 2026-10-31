from rest_framework import serializers


class TimeStampedSerializer(serializers.Serializer):
    """
    Базовый сериализатор для вывода временных меток.
    """
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
    updated_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S%z")
