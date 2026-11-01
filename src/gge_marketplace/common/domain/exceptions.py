class ValidationDomainException(Exception):
    """Исключение при валидации доменной сущности"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


class DomainException(Exception):
    """Базовое исключение для бизнес-логики"""


class ObjectNotFoundDomainException(Exception):
    """Базовое исключение для случая объект не найден"""
