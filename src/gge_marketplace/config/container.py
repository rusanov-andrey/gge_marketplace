from gge_marketplace.catalog.application.product import CreateProductUseCase, DeleteProductUseCase, UpdateProductUseCase
from gge_marketplace.catalog.infrastructure.repositories import DjangoProductRepository


class AppContainer:
    def __init__(self):
        self.product_repository = DjangoProductRepository()

    def create_product_use_case(self) -> CreateProductUseCase:
        return CreateProductUseCase(repository=self.product_repository)

    def update_product_use_case(self) -> UpdateProductUseCase:
        return UpdateProductUseCase(repository=self.product_repository)

    def delete_product_use_case(self) -> DeleteProductUseCase:
        return DeleteProductUseCase(repository=self.product_repository)


container = AppContainer()
