from gge_marketplace.common.domain.exceptions import ObjectNotFoundDomainException


class ProductNotFoundDomainException(ObjectNotFoundDomainException):
    """Товар не найден в системе"""
    def __init__(self, product_id: int | None):
        self.product_id = product_id
        super().__init__(f"Товар с id={product_id} не найден.")
