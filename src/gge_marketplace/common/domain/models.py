import datetime

import attrs


@attrs.define
class Timestamped:
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
