from django.core.exceptions import ValidationError
from django.db import models


class PipelineTask(models.Model):
    class State(models.TextChoices):
        NEW = 'new', 'Новая'
        INITIALIZED = 'initialized', 'Инициализирована'
        EXTRACTING = 'extracting', 'Загрузка'
        EXTRACTED = 'extracted', 'Загружено'
        TRANSFORMING = 'transforming', 'Трансформация'
        SUCCEED = 'succeed', 'Завершена успешно'
        ERROR = 'error', 'Завершена с ошибкой'

    class PipelineType(models.TextChoices):
        IMPORT_ORDERS = 'import_orders', 'Импорт заказов'

    pipeline_type = models.CharField(max_length=64, choices=PipelineType.choices, verbose_name='Тип процесса импорта')
    state = models.CharField(max_length=20, choices=State.choices, default=State.NEW, verbose_name='Статус')
    progress = models.IntegerField(default=0, verbose_name='Прогресс (%)')
    params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Параметры задачи',
        help_text='JSON с конфигурацией: пути к файлам, s3-бакеты, эндпоинты и т.д.'
    )

    class Meta:
        app_label = 'gge_marketplace_pipelines'
        verbose_name = 'Задача пайплайна'
        verbose_name_plural = 'Задачи пайплайнов'

    def initialize_with_file(self, file_path: str, original_name: str | None, file_size_bytes: int | None) -> None:
        if self.state != self.State.NEW:
            raise ValidationError(f"Нельзя загрузить файл. Задача находится в статусе: {self.state}")

        self.params = {
            "file_path": file_path,
            "original_name": original_name,
            "file_size_bytes": file_size_bytes
        }
        self.state = self.State.INITIALIZED


class StagingOrderItem(models.Model):
    class State(models.TextChoices):
        NEW = 'new', 'Новая'
        PROCESSED = 'processed', 'Обработано'
        ERROR = 'error', 'Ошибка'

    task = models.ForeignKey(
        'PipelineTask',
        on_delete=models.CASCADE,
        related_name='staging_orders_items',
        db_index=True,
        verbose_name='Задача импорта'
    )
    order_external_id = models.CharField(max_length=64, db_index=True, verbose_name='Внешний идентификатор заказа')
    user_email = models.CharField(max_length=255, verbose_name='Email')
    product_sku = models.CharField(max_length=64, verbose_name='Артикул')
    quantity = models.CharField(max_length=64, verbose_name='Количество')
    price_on_buy = models.CharField(max_length=64, verbose_name='Цена при покупке')
    state = models.CharField(max_length=20, choices=State.choices, verbose_name='Статус обработки')
    error_message = models.TextField(blank=True, default='', verbose_name='Сообщение об ошибке')

    class Meta:
        app_label = 'gge_marketplace_pipelines'
        verbose_name = 'Staging Order Item'
        verbose_name_plural = 'Staging Order Items'

