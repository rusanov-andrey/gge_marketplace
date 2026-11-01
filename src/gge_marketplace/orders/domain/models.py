import attrs

from gge_marketplace.common.domain.models import Timestamped

from .exceptions import OrderItemNotFoundDomainException


@attrs.define(kw_only=True)
class OrderItem:
    id: int | None = None
    product_id: int
    quantity: int
    price_on_buy: float


@attrs.define(kw_only=True)
class Order(Timestamped):
    id: int | None = None
    total_price: float
    user_id: int
    items: list[OrderItem]

    def update_total_price(self):
        self.total_price = sum(item.price_on_buy for item in self.items)

    def add_item(self, item: OrderItem):
        self.items.append(item)
        self.update_total_price()

    def get_item(self, item_id: int) -> OrderItem:
        for item in self.items:
            if item.id == item_id:
                return item

        raise OrderItemNotFoundDomainException(self.id, item_id)

    def get_last_item(self) -> OrderItem | None:
        max_id = 0
        offset = None
        for i, item in enumerate(self.items):
            if item.id is not None and item.id > max_id:
                max_id = item.id
                offset = i

        return self.items[offset] if offset is not None else None

    def update_item(self, item_id: int, product_id: int, quantity: int, price_on_buy: float):
        item = self.get_item(item_id)
        item.product_id = product_id
        item.quantity = quantity
        item.price_on_buy = price_on_buy

        self.update_total_price()

    def delete_item(self, item_id: int) -> OrderItem:
        item = self.get_item(item_id)
        self.items.remove(item)
        self.update_total_price()

        return item
