class DomainValidationError(Exception):
    """Исключение при валидации доменной сущности"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(message)


class DomainError(Exception):
    """Базовое исключение для бизнес-логики"""
    pass


class DomainObjectNotFoundError(Exception):
    """Базовое исключение для случая объект не найден"""
    pass
