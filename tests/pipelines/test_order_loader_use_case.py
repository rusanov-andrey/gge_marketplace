import pytest
from unittest.mock import Mock, MagicMock

from gge_marketplace.pipelines.models import PipelineTask, StagingOrderItem
from gge_marketplace.pipelines.application.order_loader import LoadOrdersFromXlsxToStagingUseCase


class MockXlsxIterator:
    """Фейковый итератор для подмены реального openpyxl."""

    def __init__(self, data_rows: list[dict], progress_value: float = 100.0):
        self.data_rows = data_rows
        self._progress = progress_value

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def progress(self) -> float:
        return self._progress

    def __iter__(self):
        return iter(self.data_rows)


@pytest.fixture
def mock_storage():
    """Мок для инфраструктурного хранилища файлов."""
    storage = MagicMock()
    # Эмулируем контекстный менеджер при вызове open_task_file
    storage.open_task_file.return_value.__enter__.return_value = Mock()
    return storage


@pytest.fixture
def mock_uow():
    """Мок для Unit of Work."""
    uow = MagicMock()
    uow.__enter__.return_value = uow
    return uow


@pytest.mark.django_db
def test_execute_success(mock_uow, mock_storage):
    """Успешный сценарий: извлечение данных, bulk_create и обновление статусов."""
    # 1. Готовим задачу в тестовой БД
    task = PipelineTask.objects.create(
        state=PipelineTask.State.NEW,
        progress=0,
        params={"file_path": "import/orders_test.xlsx"}
    )

    # 2. Заготавливаем фейковые строки, которые «якобы» прочитали из Excel
    fake_rows = [
        {
            'order_id': 'EXT-1', 'user_email': 'user1@test.com',
            'sku': 'SKU-A', 'quantity': '2', 'price_on_buy': '100.0'
        },
        {
            'order_id': 'EXT-2', 'user_email': 'user2@test.com',
            'sku': 'SKU-B', 'quantity': '1', 'price_on_buy': '250.5'
        }
    ]

    # Фабрика возвращает наш MockXlsxIterator со строками
    def fake_iterator_factory(file, headers):
        return MockXlsxIterator(data_rows=fake_rows, progress_value=100.0)

    # 3. Инициализируем UseCase и передаем наши заглушки
    use_case = LoadOrdersFromXlsxToStagingUseCase(
        uow=mock_uow,
        xlsx_iterator_factory=fake_iterator_factory,
        storage_service=mock_storage
    )

    # 4. Выполняем сценарий
    use_case.execute(task.id)

    # 5. Проверяем результат в БД Staging
    staging_items = StagingOrderItem.objects.filter(task=task)
    assert staging_items.count() == 2

    item_1 = staging_items.get(order_external_id='EXT-1')
    assert item_1.product_sku == 'SKU-A'
    assert item_1.state == StagingOrderItem.State.NEW

    # 6. Проверяем, что состояние задачи изменилось на EXTRACTED, а прогресс стал равен 50%
    task.refresh_from_db()
    assert task.state == PipelineTask.State.EXTRACTED
    assert task.progress == 50

    # 7. Проверяем, что файл был удален из хранилища по окончании
    mock_storage.delete_file.assert_called_once_with("import/orders_test.xlsx")


@pytest.mark.django_db
def test_execute_flushes_by_batches(mock_uow, mock_storage):
    """Проверка разбиения на чанки (BATCH_SIZE)."""
    task = PipelineTask.objects.create(
        state=PipelineTask.State.NEW,
        params={"file_path": "import/orders_large.xlsx"}
    )

    # Генерируем 3 строки
    fake_rows = [
                    {'order_id': '1', 'user_email': 'a@b.com', 'sku': 'S', 'quantity': '1', 'price_on_buy': '1'}
                ] * 3

    def fake_iterator_factory(file, headers):
        return MockXlsxIterator(data_rows=fake_rows)

    use_case = LoadOrdersFromXlsxToStagingUseCase(
        uow=mock_uow,
        xlsx_iterator_factory=fake_iterator_factory,
        storage_service=mock_storage
    )

    # Искусственно уменьшаем размер батча до 2, чтобы проверить триггер разделения чанков
    use_case.BATCH_SIZE = 2

    use_case.execute(task.id)

    # В базе всё равно должно оказаться 3 записи (2 сбросились в цикле, 1 — в остатке после цикла)
    assert StagingOrderItem.objects.filter(task=task).count() == 3


@pytest.mark.django_db
def test_execute_raises_error_if_no_file_path(mock_uow, mock_storage):
    """Если в параметрах задачи нет пути к файлу, должно бросаться исключение."""
    task = PipelineTask.objects.create(
        state=PipelineTask.State.NEW,
        params={}  # Пустые параметры без file_path
    )

    use_case = LoadOrdersFromXlsxToStagingUseCase(
        uow=mock_uow,
        xlsx_iterator_factory=Mock(),
        storage_service=mock_storage
    )

    with pytest.raises(ValueError, match=f"Отсутствует имя файла в задаче {task.id}"):
        use_case.execute(task.id)
