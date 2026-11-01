from django.contrib.auth import get_user_model

from gge_marketplace.common.domain.exceptions import ValidationDomainException
from gge_marketplace.common.infrastructure.repositories import translate_db_errors
from gge_marketplace.orders.domain.exceptions import OrderNotFoundDomainException
from gge_marketplace.orders.domain.models import Order, OrderItem
from gge_marketplace.orders.domain.repositories import OrderRepository
from gge_marketplace.orders.infrastructure.models import Order as DbOrder

User = get_user_model()


class DjangoOrderRepository(OrderRepository):
    def get_all(self) -> list[Order]:
        db_orders = DbOrder.objects.prefetch_related('items').all()
        return [
            OrderMapper.to_domain(db_order)
            for db_order in db_orders
        ]

    def get_by_id(self, order_id) -> Order:
        try:
            db_order: DbOrder = DbOrder.objects.prefetch_related('items').get(pk=order_id)
        except DbOrder.DoesNotExist:
            raise OrderNotFoundDomainException(order_id)

        return OrderMapper.to_domain(db_order)

    def get_by_user(self, user_id: str) -> list[Order]:
        pass

    @translate_db_errors({
        'foreign key constraint failed': ValidationDomainException(field='user_id', message='Пользователь не найден'),
    })
    def add(self, order: Order) -> Order:
        db_order = DbOrder()
        db_order = OrderMapper.to_orm(order, db_order)
        db_order.save()

        OrderMapper.items_to_orm(order, db_order)

        return OrderMapper.to_domain(db_order)

    @translate_db_errors({
        'foreign key constraint failed': ValidationDomainException(field='user_id', message='Пользователь не найден'),
    })
    def update(self, order: Order) -> Order:
        try:
            assert order.id is not None
            db_order: DbOrder = DbOrder.objects.prefetch_related('items').get(pk=order.id)
        except DbOrder.DoesNotExist:
            raise OrderNotFoundDomainException(order.id)

        db_order = OrderMapper.to_orm(order, db_order)
        db_order.save()

        OrderMapper.items_to_orm(order, db_order)
        db_order = DbOrder.objects.prefetch_related('items').get(pk=db_order.id)

        return OrderMapper.to_domain(db_order)

    def delete(self, order_id: int) -> Order:
        try:
            db_order: DbOrder = DbOrder.objects.prefetch_related('items').get(pk=order_id)
        except DbOrder.DoesNotExist:
            raise OrderNotFoundDomainException(order_id)

        order = OrderMapper.to_domain(db_order)

        db_order.delete()
        db_order.save()

        return order


class OrderMapper:
    @staticmethod
    def to_orm(order: Order, db_order: DbOrder) -> DbOrder:
        db_order.user_id = order.user_id
        db_order.total_price = order.total_price
        return db_order

    @staticmethod
    def items_to_orm(order: Order, db_order: DbOrder) -> None:
        current_product_ids = [item.product_id for item in order.items]

        db_order.items.exclude(product_id__in=current_product_ids).delete()

        for item in order.items:
            db_order.items.update_or_create(
                product_id=item.product_id,
                defaults={
                    'quantity': item.quantity,
                    'price_on_buy': item.price_on_buy
                }
            )

    @staticmethod
    def to_domain(db_order: DbOrder) -> Order:
        return Order(
            id=db_order.id,
            user_id=db_order.user_id,
            total_price=db_order.total_price,
            items=[
                OrderItem(
                    id=item_db.id,
                    product_id=item_db.product_id,
                    quantity=item_db.quantity,
                    price_on_buy=item_db.price_on_buy
                )
                for item_db in db_order.items.all()
            ],
            created_at=db_order.created_at,
            updated_at=db_order.updated_at,
        )
