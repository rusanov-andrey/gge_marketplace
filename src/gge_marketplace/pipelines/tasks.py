import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)


@shared_task(
    name="pipeline.tasks.run_import_pipeline",
    queue="heavy_pipelines"
)
def run_import_pipeline_task(task_id: int):
    logger.info(f"Запуск фонового пайплайна для задачи #{task_id}")

    # Лениво импортируем контейнер/модели, чтобы избежать циклической зависимости при старте Celery
    from gge_marketplace.config.container import container

    from .models import PipelineTask

    try:
        PipelineTask.objects.get(pk=task_id)

        logger.info(f"Этап 1: Импорт в staging для задачи #{task_id}")
        extract_use_case = container.load_orders_from_xlsx_to_staging_use_case()
        extract_use_case.execute(task_id=task_id)

        logger.info(f"Этап 2: Трансформация в заказы для задачи #{task_id}")
        transform_use_case = container.transform_staging_to_orders_use_case()
        transform_use_case.execute(task_id=task_id)

        logger.info(f"Пайплайн для задачи #{task_id} успешно завершен.")

    except ObjectDoesNotExist:
        logger.error(f"Задача #{task_id} не найдена.")
    except Exception:
        logger.exception(f"Критическая ошибка пайплайна #{task_id}")

        from .models import PipelineTask
        PipelineTask.objects.filter(pk=task_id).update(
            state='error',
        )
