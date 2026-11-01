from django.db import models

from gge_marketplace.common.infrastructure.models import TimeStampedModel


class Product(TimeStampedModel):
    stock_keeping_unit = models.CharField(max_length=64, unique=True, verbose_name='Артикул')
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.CharField(max_length=1024, verbose_name='Описание')
    price = models.FloatField(verbose_name='Цена')

    class Meta:
        app_label = 'gge_marketplace_catalog'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
