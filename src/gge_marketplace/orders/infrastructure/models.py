from django.conf import settings
from django.db import models

from gge_marketplace.catalog.infrastructure.models import Product
from gge_marketplace.common.infrastructure.models import TimeStampedModel


class Order(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Покупатель"
    )
    total_price = models.FloatField(verbose_name="Общая стоимость")

    class Meta:
        app_label = 'gge_marketplace_orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name="Товар"
    )
    quantity = models.IntegerField(verbose_name="Количество")
    price_on_buy = models.FloatField(verbose_name="Цена при покупке")

    class Meta:
        app_label = 'gge_marketplace_orders'
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'
        unique_together = ('order', 'product')
