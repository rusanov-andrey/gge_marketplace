from django.db import transaction

from gge_marketplace.common.application.unit_of_work import UnitOfWork


class DjangoUnitOfWork(UnitOfWork):
    def __enter__(self):
        transaction.set_autocommit(False)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            transaction.set_autocommit(True)

    def commit(self):
        transaction.commit()

    def rollback(self):
        transaction.rollback()
