import datetime

from gge_marketplace.orders.domain.repositories import OrderRepository


class GetProductSalesAnalyticsUseCase:
    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository

    def execute(self, date_from: datetime.date, date_to: datetime.date):
        if date_from > date_to:
            raise ValueError("Дата начала (date_from) не может быть больше даты окончания (date_to)")

        return self.order_repository.get_product_sales_analytics(date_from, date_to)
