from gge_marketplace.common.domain.exceptions import ObjectNotFoundDomainException


class OrderNotFoundDomainException(ObjectNotFoundDomainException):
    """Заказ не найден в системе"""
    def __init__(self, order_id: int | None):
        self.order_id = order_id
        super().__init__(f"Заказ с id={order_id} не найден.")


class OrderItemNotFoundDomainException(ObjectNotFoundDomainException):
    """Позиция заказа не найдена"""
    def __init__(self, order_id: int | None, item_id: int | None):
        self.order_id = order_id
        super().__init__(f"В заказе с id={order_id} не найдена позиция с id={item_id}.")
