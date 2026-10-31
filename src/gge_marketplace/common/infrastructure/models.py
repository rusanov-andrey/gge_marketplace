from django.db import models


class TimeStampedModel(models.Model):
    """
    Абстрактная базовая модель для автоматического
    логирования времени создания и обновления записей в БД.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        abstract = True
