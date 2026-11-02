import datetime
from abc import ABC, abstractmethod

from .models import Order, ProductAnalyticsItem


class OrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: int) -> Order:
        pass

    @abstractmethod
    def get_all(self) -> list[Order]:
        pass

    @abstractmethod
    def add(self, order: Order) -> Order:
        pass

    @abstractmethod
    def update(self, order: Order) -> Order:
        pass

    @abstractmethod
    def delete(self, order_id: int) -> Order:
        pass

    @abstractmethod
    def get_product_sales_analytics(
            self,
            date_from: datetime.date,
            date_to: datetime.date
    ) -> list[ProductAnalyticsItem]:
        pass
