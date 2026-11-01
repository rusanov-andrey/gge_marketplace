from gge_marketplace.catalog.application.product import (
    CreateProductUseCase,
    DeleteProductUseCase,
    UpdateProductUseCase,
)
from gge_marketplace.catalog.infrastructure.repositories import DjangoProductRepository
from gge_marketplace.common.infrastructure.unit_of_work import DjangoUnitOfWork
from gge_marketplace.orders.application.order import (
    AddItemToOrderUseCase,
    CreateOrderUseCase,
    DeleteItemFromOrderUseCase,
    DeleteOrderUseCase,
    GetItemFromOrderUseCase,
    UpdateItemInOrderUseCase,
)
from gge_marketplace.orders.infrastructure.repositories import DjangoOrderRepository


class AppContainer:
    def __init__(self):
        self.product_repository = DjangoProductRepository()
        self.order_repository = DjangoOrderRepository()
        self.uow = DjangoUnitOfWork()

    def create_product_use_case(self) -> CreateProductUseCase:
        return CreateProductUseCase(repository=self.product_repository)

    def update_product_use_case(self) -> UpdateProductUseCase:
        return UpdateProductUseCase(repository=self.product_repository)

    def delete_product_use_case(self) -> DeleteProductUseCase:
        return DeleteProductUseCase(repository=self.product_repository)

    def create_order_use_case(self) -> CreateOrderUseCase:
        return CreateOrderUseCase(repository=self.order_repository)

    def delete_order_use_case(self) -> DeleteOrderUseCase:
        return DeleteOrderUseCase(repository=self.order_repository)

    def add_item_to_order_use_case(self) -> AddItemToOrderUseCase:
        return AddItemToOrderUseCase(uow=self.uow, repository=self.order_repository)

    def update_item_in_order_use_case(self) -> UpdateItemInOrderUseCase:
        return UpdateItemInOrderUseCase(uow=self.uow, repository=self.order_repository)

    def delete_item_from_order_use_case(self) -> DeleteItemFromOrderUseCase:
        return DeleteItemFromOrderUseCase(uow=self.uow, repository=self.order_repository)

    def get_item_from_order_use_case(self) -> GetItemFromOrderUseCase:
        return GetItemFromOrderUseCase(repository=self.order_repository)


container = AppContainer()
