from abc import ABC, abstractmethod
from collections.abc import Iterator

from .models import Product


class ProductRepository(ABC):
    @abstractmethod
    def get_by_id(self, product_id: int) -> Product:
        pass

    @abstractmethod
    def get_all(self) -> Iterator[Product]:
        pass

    @abstractmethod
    def get_by_stock_keeping_unit(self, stock_keeping_unit: str) -> Product | None:
        pass

    @abstractmethod
    def get_by_stock_keeping_units(self, stock_keeping_unit: set[str]) -> Iterator[Product]:
        pass

    @abstractmethod
    def add(self, product: Product) -> Product:
        pass

    @abstractmethod
    def update(self, product: Product) -> Product:
        pass

    @abstractmethod
    def delete(self, product_id: int) -> Product:
        pass

    @abstractmethod
    def is_exists_by_stock_keeping_unit(self, stock_keeping_unit: str) -> bool:
        pass

