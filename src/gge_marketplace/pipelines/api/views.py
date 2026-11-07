from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from gge_marketplace.config.container import container
from gge_marketplace.pipelines.models import PipelineTask

from .serializers import FileUploadSerializer, PipelineTaskSerializer


@extend_schema_view(
    list=extend_schema(
        summary="Получить список задач",
        responses={200: PipelineTaskSerializer(many=True)}
    ),
    create=extend_schema(
        summary="Создать задачу на запуск pipeline",
        request=PipelineTaskSerializer,
        responses={201: PipelineTaskSerializer}
    ),
    retrieve=extend_schema(
        summary="Получить получить информацию по задаче",
        description="Метод позволяет следить за изменением статуса задачи",
        responses={200: PipelineTaskSerializer}
    ),
    update=extend_schema(
        summary="Обновить информацию по задаче",
        request=PipelineTaskSerializer,
        responses={200: PipelineTaskSerializer}
    ),
    partial_update=extend_schema(
        summary="Обновить информацию по задаче",
        request=PipelineTaskSerializer,
        responses={200: PipelineTaskSerializer}
    ),
    destroy=extend_schema(
        summary="Удалить задачу",
        responses={200: PipelineTaskSerializer}
    ),
)
class PipelineViewSet(ModelViewSet):
    queryset = PipelineTask.objects.all().order_by('-id')
    serializer_class = PipelineTaskSerializer

    @extend_schema(
        summary="Загрузка файла с исходными данными",
        description="Позволяет загрузит файл с данными и инициировать фоновый импорт.",
        request=FileUploadSerializer,
        responses={200: PipelineTaskSerializer()}
    )
    @action(detail=True, methods=['post'], serializer_class=FileUploadSerializer)
    def upload(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data['file']

        use_case = container.initialize_pipeline_use_case()
        try:
            task = use_case.execute(task_id=pk, uploaded_file=uploaded_file)
        except PipelineTask.DoesNotExist:
            return Response({"error": "Задача не найдена"}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({"error": e.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": "Файл успешно загружен. Задача передана в Celery.",
                "task": PipelineTaskSerializer(task).data
            },
            status=status.HTTP_200_OK
        )
