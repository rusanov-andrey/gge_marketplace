from gge_marketplace.catalog.domain.models import Product
from gge_marketplace.catalog.domain.repositories import ProductRepository
from gge_marketplace.common.infrastructure.exceptions import DomainValidationError


class CreateProductUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def execute(self, *, stock_keeping_unit: str, title: str, description: str, price: float) -> Product:
        if self.repository.is_exists_by_stock_keeping_unit(stock_keeping_unit):
            raise DomainValidationError(field='stock_keeping_unit', message=f'Артикул "{stock_keeping_unit}" уже занят')
        product = Product(stock_keeping_unit=stock_keeping_unit, title=title, description=description, price=price)
        return self.repository.add(product)


class UpdateProductUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def execute(self, *, id: int, stock_keeping_unit: str, title: str, description: str, price: float) -> Product:
        product = Product(
            id=id,
            stock_keeping_unit=stock_keeping_unit,
            title=title,
            description=description,
            price=price
        )
        return self.repository.update(product)


class DeleteProductUseCase:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def execute(self, *, id: int) -> Product:
        return self.repository.delete(id)
