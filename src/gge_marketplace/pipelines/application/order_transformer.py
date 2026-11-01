import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.query import QuerySet

from gge_marketplace.catalog.domain.repositories import ProductRepository
from gge_marketplace.common.application.unit_of_work import UnitOfWork
from gge_marketplace.orders.domain.models import Order, OrderItem
from gge_marketplace.orders.domain.repositories import OrderRepository
from gge_marketplace.pipelines.models import PipelineTask, StagingOrderItem

logger = logging.getLogger(__name__)
User = get_user_model()


class TransformStagingToOrdersUseCase:
    """
    Прикладной сервис (Use Case) для трансформации данных из Staging-слоя
    в доменные сущности заказов и сохранения их через DDD-репозитории.
    """

    CHUNK_SIZE = 100  # Обрабатываем по 100 уникальных внешних заказов за итерацию

    def __init__(self, uow: UnitOfWork, product_repository: ProductRepository, order_repository: OrderRepository):
        self.product_repository = product_repository
        self.order_repository = order_repository
        self.uow = uow

    def execute(self, task_id: int) -> None:
        task = PipelineTask.objects.get(pk=task_id)

        if task.state != PipelineTask.State.TRANSFORMING:
            task.state = PipelineTask.State.TRANSFORMING
            task.save(update_fields=['state'])

        while True:
            # 1. Получаем чанк уникальных ID внешних заказов, которые еще не обработаны
            external_order_ids = (
                StagingOrderItem.objects.filter(task=task, state=StagingOrderItem.State.NEW)
                .values_list('order_external_id', flat=True)
                .distinct()[:self.CHUNK_SIZE]
            )

            # Если новых заказов больше нет — выходим из цикла
            if not external_order_ids:
                break

            # 2. Выкачиваем все строки стейджинга для выбранных заказов
            staging_rows: QuerySet[StagingOrderItem] = StagingOrderItem.objects.filter(
                task=task,
                order_external_id__in=external_order_ids
            )

            # Группируем строки по order_external_id в оперативной памяти для обработки
            grouped_orders: dict[str, list[StagingOrderItem]] = {}
            for row in staging_rows:
                grouped_orders.setdefault(row.order_external_id, []).append(row)

            # 3. Обрабатываем каждый внешний заказ индивидуально внутри своей транзакции
            for ext_order_id, rows in grouped_orders.items():
                self._process_single_order(ext_order_id, rows)

        # Проверяем, остались ли ошибки. Если ошибок нет, закрываем таску
        has_errors = StagingOrderItem.objects.filter(task=task, state=StagingOrderItem.State.ERROR).exists()
        task.state = PipelineTask.State.SUCCEED if not has_errors else PipelineTask.State.ERROR
        task.progress = 100
        task.save(update_fields=['state', 'progress'])

    def _process_single_order(self, ext_order_id: str, rows: list[StagingOrderItem]) -> None:
        """Обрабатывает один заказ атомарно. Успех — удаление, ошибка — статус ERROR."""
        # Используем транзакцию Django только для этого заказа
        # Если внутри блока произойдет Exception, Django откатит изменения в БД для этого заказа
        try:
            with self.uow:
                # Инициализируем данные для проверки
                user_id = self._validate_and_get_user_id(ext_order_id, rows)

                # Собираем элементы заказа (схлопывая дублирующиеся SKU)
                aggregated_items = self._aggregate_order_items(rows)

                # Создаем доменную сущность Order
                order = Order(
                    user_id=user_id,
                    total_price=0.0,
                    items=[]
                )

                # Наполняем доменный заказ позициями
                for item_data in aggregated_items.values():
                    order_item = OrderItem(
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        price_on_buy=item_data['price_on_buy']
                    )
                    order.add_item(order_item)

                # Сохраняем через DDD-репозиторий в боевую БД
                self.order_repository.add(order)

                # Успешно импортировано -> удаляем строки из стейджинга, чтобы освободить место
                # (В соответствии с вашим условием перезапускаемости)
                StagingOrderItem.objects.filter(id__in=[r.id for r in rows]).delete()

        except ValidationError as e:
            # Бизнес-ошибка (пользователь/товар не найден или некорректные типы)
            self._mark_order_as_error(rows, str(e.message))
        except Exception as e:
            # Системная непредвиденная ошибка
            logger.exception(f"Критическая ошибка трансформации заказа {ext_order_id}")
            self._mark_order_as_error(rows, f"Системная ошибка: {e!s}")

    def _validate_and_get_user_id(self, ext_order_id: str, rows: list[StagingOrderItem]) -> int:
        """Проверяет сквозной email пользователя и ищет его в БД."""
        emails = {row.user_email for row in rows if row.user_email}

        if len(emails) != 1:
            raise ValidationError(
                f"Брак: В позициях заказа {ext_order_id} указано несколько разных пользователей или email пуст.")

        email = emails.pop()
        try:
            user = User.objects.get(email=email)
            return user.id
        except User.DoesNotExist:
            raise ValidationError(f"Брак: Пользователь с email {email} не найден в справочнике.")

    def _aggregate_order_items(self, rows: list[StagingOrderItem]) -> dict:
        """
        Проверяет типы, наличие товаров и складывает позиции с одинаковым SKU.
        """
        aggregated: dict[int, dict] = {}  # Словарь для группировки: {product_id: {quantity: int, price_on_buy: float}}

        for row in rows:
            # 1. Валидация числовых значений
            try:
                qty = int(row.quantity)
                price = float(row.price_on_buy)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Брак: Ошибка приведения типов в строке SKU {row.product_sku}. "
                    f"Количество: '{row.quantity}', Цена: '{row.price_on_buy}'"
                )

            # 2. Поиск товара по SKU через репозиторий товаров
            product = self.product_repository.get_by_stock_keeping_unit(row.product_sku)
            if not product or product.id is None:
                raise ValidationError(f"Брак: Товар с SKU {row.product_sku} не найден в справочнике.")

            product_id = product.id

            # 3. Агрегация: если товар уже есть в заказе — увеличиваем его количество
            if product_id in aggregated:
                aggregated[product_id]['quantity'] += qty
                # Обновляем цену последней прочитанной строкой
                aggregated[product_id]['price_on_buy'] = price
            else:
                # Если товар встретился первый раз — инициализируем запись (Запись в словарь)
                aggregated[product_id] = {
                    'product_id': product_id,
                    'quantity': qty,
                    'price_on_buy': price
                }

        return aggregated

    def _mark_order_as_error(self, rows: list[StagingOrderItem], message: str) -> None:
        """Помечает всю пачку строк внешнего заказа ошибкой."""
        row_ids = [row.id for row in rows]
        StagingOrderItem.objects.filter(id__in=row_ids).update(
            state=StagingOrderItem.State.ERROR,
            error_message=message
        )
