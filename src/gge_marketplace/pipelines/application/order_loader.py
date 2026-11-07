from typing import Callable

from django.core.files import File
from django.core.files.uploadedfile import UploadedFile

from gge_marketplace.common.application.unit_of_work import UnitOfWork
from gge_marketplace.pipelines.infrastructure.file_storage import TaskFileStorage
from gge_marketplace.pipelines.infrastructure.xlsx_reader import XlsxIterator
from gge_marketplace.pipelines.models import PipelineTask, StagingOrderItem
from gge_marketplace.pipelines.tasks import run_import_pipeline_task


class InitializePipelineUseCase:
    def __init__(self, uow: UnitOfWork, storage_service: TaskFileStorage):
        self.storage_service = storage_service
        self.uow = uow

    def execute(self, task_id: int, uploaded_file: UploadedFile) -> PipelineTask:
        with self.uow:
            task: PipelineTask = PipelineTask.objects.select_for_update().get(pk=task_id)

            file_storage_path = self.storage_service.save_task_file(
                task_id=task.id,
                uploaded_file=uploaded_file
            )

            try:
                task.initialize_with_file(
                    file_path=file_storage_path,
                    original_name=uploaded_file.name,
                    file_size_bytes=uploaded_file.size
                )
            except Exception:
                self.storage_service.delete_file(file_storage_path)
                raise

            task.save()

        run_import_pipeline_task.delay(task.id)

        return task


class LoadOrdersFromXlsxToStagingUseCase:
    BATCH_SIZE = 5000  # Размер чанка для сохранения в БД
    MAX_PROGRESS_VALUE = 50  # Максимальное значение прогресса задачи. Остальное -- при импорте из staging в orders

    def __init__(
            self,
            uow: UnitOfWork,
            storage_service: TaskFileStorage,
            xlsx_iterator_factory: Callable[[File, list[str]], XlsxIterator] = XlsxIterator,
    ):
        self.storage_service = storage_service
        self.uow = uow
        self.xlsx_iterator_factory = xlsx_iterator_factory
        self.file_headers = ['order_id', 'user_email', 'sku', 'quantity', 'price_on_buy']

    def execute(self, task_id: int) -> None:
        task: PipelineTask = PipelineTask.objects.get(pk=task_id)

        if task.state != PipelineTask.State.EXTRACTING:
            task.state = PipelineTask.State.EXTRACTING
            task.save(update_fields=['state'])

        file_path = task.params.get('file_path')

        if not file_path:
            raise ValueError(f"Отсутствует имя файла в задаче {task_id}")

        StagingOrderItem.objects.filter(task_id=task_id).delete()

        with self.storage_service.open_task_file(file_path) as f:
            # Построчно читаем данные чанками
            staging_pool = []
            with self.xlsx_iterator_factory(f, self.file_headers) as xslt_iterator:
                for row in xslt_iterator:
                    item = StagingOrderItem(
                        task=task,
                        order_external_id=row['order_id'],
                        user_email=row['user_email'],
                        product_sku=row['sku'],
                        quantity=row['quantity'],
                        price_on_buy=row['price_on_buy'],
                        state=StagingOrderItem.State.NEW
                    )
                    staging_pool.append(item)

                    # Если набрался размер пакета, сбрасываем в базу
                    if len(staging_pool) >= self.BATCH_SIZE:
                        self._flush_batch(staging_pool, task, xslt_iterator.progress)
                        staging_pool = []

                # Сбрасываем остаток, если он есть
                if staging_pool:
                    self._flush_batch(staging_pool, task, xslt_iterator.progress)

        task.state = PipelineTask.State.EXTRACTED
        task.progress = self.MAX_PROGRESS_VALUE
        task.save(update_fields=['state', 'progress'])
        self.storage_service.delete_file(file_path)

    def _flush_batch(self, items: list, task: PipelineTask, progress: float) -> None:
        """Вспомогательный метод для атомарной записи пакета строк и обновления прогресса."""
        with self.uow:
            StagingOrderItem.objects.bulk_create(items)

            # Считаем приблизительный прогресс
            calculated_progress = int(progress * self.MAX_PROGRESS_VALUE)

            task.progress = calculated_progress
            task.save(update_fields=['progress'])
