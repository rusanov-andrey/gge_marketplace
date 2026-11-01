from rest_framework import serializers

from gge_marketplace.pipelines.models import PipelineTask


class PipelineTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineTask
        fields = [
            'id',
            'pipeline_type',
            'state',
            'progress',
            'params'
        ]
        read_only_fields = ['state', 'progress', 'params']


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="Физический файл для импорта (CSV/XLSX)")

