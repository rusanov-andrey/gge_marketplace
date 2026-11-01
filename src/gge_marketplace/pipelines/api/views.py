from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from gge_marketplace.config.container import container
from gge_marketplace.pipelines.models import PipelineTask

from .serializers import FileUploadSerializer, PipelineTaskSerializer


class PipelineViewSet(ModelViewSet):
    queryset = PipelineTask.objects.all().order_by('-id')
    serializer_class = PipelineTaskSerializer

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

        use_case = container.load_orders_from_xlsx_to_staging_use_case()
        use_case.execute(task_id=pk)

        use_case = container.transform_staging_to_orders_use_case()
        use_case.execute(task_id=pk)

        return Response(
            {
                "message": "Файл успешно загружен. Задача передана в Celery.",
                "task": PipelineTaskSerializer(task).data
            },
            status=status.HTTP_200_OK
        )
