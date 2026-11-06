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
    CHUNK_SIZE = 100

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
            # 1. Получаем чанк уникальных ID
            external_order_ids = list(
                StagingOrderItem.objects.filter(task=task, state=StagingOrderItem.State.NEW)
                .values_list('order_external_id', flat=True)
                .distinct()[:self.CHUNK_SIZE]
            )

            if not external_order_ids:
                break

            # 2. Выкачиваем все строки стейджинга для выбранных заказов
            staging_rows: QuerySet[StagingOrderItem] = StagingOrderItem.objects.filter(
                task=task,
                order_external_id__in=external_order_ids
            )

            emails = {row.user_email for row in staging_rows if row.user_email}
            skus = {row.product_sku for row in staging_rows if row.product_sku}

            users_map = {u.email: u.id for u in User.objects.filter(email__in=emails)}

            products_map = {}
            for prod in self.product_repository.get_by_stock_keeping_units(skus):
                if prod and prod.id:
                    products_map[prod.stock_keeping_unit] = prod.id

            # Группируем строки в памяти
            grouped_orders: dict[str, list[StagingOrderItem]] = {}
            for row in staging_rows:
                grouped_orders.setdefault(row.order_external_id, []).append(row)

            # 3. Обрабатываем каждый внешний заказ индивидуально
            for ext_order_id, rows in grouped_orders.items():
                self._process_single_order(ext_order_id, rows, users_map, products_map)

        # Финализация таски
        has_errors = StagingOrderItem.objects.filter(task=task, state=StagingOrderItem.State.ERROR).exists()
        task.state = PipelineTask.State.SUCCEED if not has_errors else PipelineTask.State.ERROR
        task.progress = 100
        task.save(update_fields=['state', 'progress'])

    def _process_single_order(
            self,
            ext_order_id: str,
            rows: list[StagingOrderItem],
            users_map: dict[str, int],
            products_map: dict[str, int]
    ) -> None:
        try:
            with self.uow:
                # Валидация пользователя по кэшированной мапе
                user_id = self._validate_and_get_user_id(ext_order_id, rows, users_map)

                # Агрегация позиций по кэшированной мапе товаров
                aggregated_items = self._aggregate_order_items(rows, products_map)

                order = Order(
                    user_id=user_id,
                    total_price=0.0,
                    items=[]
                )

                for item_data in aggregated_items.values():
                    order_item = OrderItem(
                        product_id=item_data['product_id'],
                        quantity=item_data['quantity'],
                        price_on_buy=item_data['price_on_buy']
                    )
                    order.add_item(order_item)

                self.order_repository.add(order)

                # Очищаем стейджинг
                StagingOrderItem.objects.filter(id__in=[r.id for r in rows]).delete()

        except ValidationError as e:
            self._mark_order_as_error(rows, str(e))
        except Exception as e:
            logger.exception(f"Критическая ошибка трансформации заказа {ext_order_id}")
            try:
                self._mark_order_as_error(rows, f"Системная ошибка: {e!s}")
            except Exception as database_error:
                logger.critical(f"Не удалось обновить статус ошибки в БД: {database_error}")
                raise

    def _validate_and_get_user_id(
            self,
            ext_order_id: str,
            rows: list[StagingOrderItem],
            users_map: dict[str, int],
    ) -> int:
        emails = {row.user_email for row in rows if row.user_email}

        if len(emails) != 1:
            raise ValidationError(
                f"Брак: В позициях заказа {ext_order_id} указано несколько разных пользователей или email пуст."
            )

        email = emails.pop()
        user_id = users_map.get(email)
        if not user_id:
            raise ValidationError(f"Брак: Пользователь с email {email} не найден в справочнике.")
        return user_id

    def _aggregate_order_items(self, rows: list[StagingOrderItem], products_map: dict[str, int]) -> dict:
        aggregated: dict[int, dict] = {}

        for row in rows:
            try:
                qty = int(row.quantity)
                price = float(row.price_on_buy)
            except (ValueError, TypeError):
                raise ValidationError(
                    f"Брак: Ошибка приведения типов в строке SKU {row.product_sku}. "
                    f"Количество: '{row.quantity}', Цена: '{row.price_on_buy}'"
                )

            product_id = products_map.get(row.product_sku)
            if not product_id:
                raise ValidationError(f"Брак: Товар с SKU {row.product_sku} не найден в справочнике.")

            if product_id in aggregated:
                aggregated[product_id]['quantity'] += qty
                aggregated[product_id]['price_on_buy'] = price
            else:
                aggregated[product_id] = {
                    'product_id': product_id,
                    'quantity': qty,
                    'price_on_buy': price
                }

        return aggregated

    def _mark_order_as_error(self, rows: list[StagingOrderItem], message: str) -> None:
        row_ids = [row.id for row in rows]
        StagingOrderItem.objects.filter(id__in=row_ids).update(
            state=StagingOrderItem.State.ERROR,
            error_message=message
        )
