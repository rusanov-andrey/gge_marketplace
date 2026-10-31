from gge_marketplace.catalog.domain.exceptions import ProductNotFoundError
from gge_marketplace.catalog.domain.models import Product
from gge_marketplace.catalog.domain.repositories import ProductRepository
from gge_marketplace.catalog.infrastructure.models import Product as DbProduct
from gge_marketplace.common.domain.exceptions import DomainValidationError
from gge_marketplace.common.infrastructure.repositories import translate_db_errors


class DjangoProductRepository(ProductRepository):
    def get_all(self) -> list[Product]:
        db_products = DbProduct.objects.all()
        return [
            ProductMapper.to_domain(db_product)
            for db_product in db_products
        ]

    def get_by_id(self, product_id) -> Product:
        try:
            db_product: DbProduct = DbProduct.objects.get(pk=product_id)
        except DbProduct.DoesNotExist:
            raise ProductNotFoundError(product_id)

        return ProductMapper.to_domain(db_product)

    def get_by_stock_keeping_unit(self, stock_keeping_unit: str) -> Product | None:
        try:
            db_product: DbProduct = DbProduct.objects.get(stock_keeping_unit=stock_keeping_unit)
        except DbProduct.DoesNotExist:
            return None

        return ProductMapper.to_domain(db_product)

    @translate_db_errors({
        'stock_keeping_unit': DomainValidationError(field='stock_keeping_unit', message='Артикул уже занят'),
    })
    def add(self, product: Product) -> Product:
        db_product: DbProduct = DbProduct.objects.create(
            stock_keeping_unit=product.stock_keeping_unit,
            title=product.title,
            description=product.description,
            price=product.price,
        )
        return ProductMapper.to_domain(db_product)

    @translate_db_errors({
        'stock_keeping_unit': DomainValidationError(field='stock_keeping_unit', message='Артикул уже занят'),
    })
    def update(self, product: Product) -> Product:
        try:
            db_product: DbProduct = DbProduct.objects.get(pk=product.id)
        except DbProduct.DoesNotExist:
            raise ProductNotFoundError(product.id)

        db_product = ProductMapper.to_orm(product, db_product)
        db_product.save()
        db_product.refresh_from_db(fields=['updated_at'])

        return ProductMapper.to_domain(db_product)

    def delete(self, product_id: int) -> Product:
        try:
            db_product: DbProduct = DbProduct.objects.get(pk=product_id)
        except DbProduct.DoesNotExist:
            raise ProductNotFoundError(product_id)

        product = ProductMapper.to_domain(db_product)

        db_product.delete()
        db_product.save()

        return product

    def is_exists_by_stock_keeping_unit(self, stock_keeping_unit: str) -> bool:
        return DbProduct.objects.filter(stock_keeping_unit=stock_keeping_unit).exists()


class ProductMapper:
    @staticmethod
    def to_orm(product: Product, db_product: DbProduct) -> DbProduct:
        db_product.stock_keeping_unit = product.stock_keeping_unit
        db_product.title = product.title
        db_product.description = product.description
        db_product.price = product.price
        return db_product

    @staticmethod
    def to_domain(db_product: DbProduct) -> Product:
        return Product(
            id=db_product.pk,
            stock_keeping_unit=db_product.stock_keeping_unit,
            title=db_product.title,
            description=db_product.description,
            price=db_product.price,
            created_at=db_product.created_at,
            updated_at=db_product.updated_at,
        )
