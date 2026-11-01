from gge_marketplace.common.application.unit_of_work import UnitOfWork
from gge_marketplace.common.domain.exceptions import ValidationDomainException
from gge_marketplace.common.infrastructure.repositories import translate_db_errors
from gge_marketplace.orders.domain.models import Order, OrderItem
from gge_marketplace.orders.domain.repositories import OrderRepository


class CreateOrderUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def execute(self, *, user_id: int) -> Order:
        order = Order(user_id=user_id, total_price=0, items=[])
        return self.repository.add(order)


class DeleteOrderUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def execute(self, *, id: int) -> Order:
        return self.repository.delete(id)


class GetItemFromOrderUseCase:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def execute(self, *, order_id: int, item_id: int) -> OrderItem:
        order = self.repository.get_by_id(order_id)
        return order.get_item(item_id)


class AddItemToOrderUseCase:
    def __init__(self, uow: UnitOfWork, repository: OrderRepository):
        self.repository = repository
        self.uow = uow

    @translate_db_errors({
        'foreign key constraint failed': ValidationDomainException(field='product_id', message='Товар не найден'),
    })
    def execute(self, *, order_id: int, product_id: int, quantity: int, price_on_buy: float) -> OrderItem:
        with self.uow:
            order = self.repository.get_by_id(order_id)
            items_amount = len(order.items)
            order.add_item(OrderItem(product_id=product_id, quantity=quantity, price_on_buy=price_on_buy))

            order = self.repository.update(order)

            added_item = order.get_last_item()
            if added_item is None or len(order.items) <= items_amount:
                raise RuntimeError('Could not add item to order')
            return added_item


class UpdateItemInOrderUseCase:
    def __init__(self, uow: UnitOfWork, repository: OrderRepository):
        self.repository = repository
        self.uow = uow

    @translate_db_errors({
        'foreign key constraint failed': ValidationDomainException(field='product_id', message='Товар не найден'),
    })
    def execute(self, *, order_id: int, item_id: int, product_id: int, quantity: int, price_on_buy: float) -> OrderItem:
        with self.uow:
            order = self.repository.get_by_id(order_id)
            order.update_item(item_id=item_id, product_id=product_id, quantity=quantity, price_on_buy=price_on_buy)

            order = self.repository.update(order)

            item = next((i for i in order.items if i.id == item_id), None)
            if item is None:
                raise RuntimeError('Could not update item in order')
            return item


class DeleteItemFromOrderUseCase:
    def __init__(self, uow: UnitOfWork, repository: OrderRepository):
        self.repository = repository
        self.uow = uow

    def execute(self, *, order_id: int, item_id: int) -> OrderItem:
        with self.uow:
            order = self.repository.get_by_id(order_id)
            item = order.delete_item(item_id)

            self.repository.update(order)

            return item
