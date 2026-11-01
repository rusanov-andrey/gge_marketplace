from abc import ABC, abstractmethod

from .models import Order


class OrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: int) -> Order:
        pass

    @abstractmethod
    def get_all(self) -> list[Order]:
        pass

    @abstractmethod
    def get_by_user(self, user_id: str) -> list[Order]:
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

