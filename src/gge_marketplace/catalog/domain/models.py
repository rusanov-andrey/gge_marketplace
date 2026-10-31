import attrs

from gge_marketplace.common.domain.models import Timestamped


@attrs.define(kw_only=True)
class Product(Timestamped):
    id: int | None = None
    stock_keeping_unit: str
    title: str
    description: str
    price: float
