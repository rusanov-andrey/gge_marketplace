from functools import wraps

from django.db import IntegrityError


def translate_db_errors(error_mapping: dict):
    """Декоратор для методов репозитория.
    Превращает системные ошибки Django/СУБД в доменные ошибки.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except IntegrityError as e:
                err_msg = (str(e.__cause__) or str(e)).lower()

                # Ищем триггер в переданном маппинге ошибок для этого метода
                for db_trigger, domain_exc in error_mapping.items():
                    if db_trigger.lower() in err_msg:
                        raise domain_exc
                # Если ошибка неизвестна — прокидываем дальше
                raise

        return wrapper

    return decorator
