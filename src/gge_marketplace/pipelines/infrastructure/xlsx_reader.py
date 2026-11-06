from collections.abc import Iterator

import openpyxl
from django.core.files import File


class XlsxIterator:
    def __init__(self, file: File, column_names: list[str]) -> None:
        self.file = file
        self.column_names = [name.strip().lower() for name in column_names]

        self._rows_iterator: Iterator | None = None
        self._workbook: openpyxl.Workbook | None = None
        self._col_map: dict[str, int] = {}
        self._total_rows = 0
        self._processed_rows = 0

    @property
    def progress(self) -> float:
        return (
            self._processed_rows / self._total_rows
            if self._total_rows > 0
            else 0
        )

    def close(self) -> None:
        if self._workbook is not None:
            self._workbook.close()
            self._workbook = None

        self._rows_iterator = None

    def __iter__(self):
        self._workbook = openpyxl.load_workbook(self.file, read_only=True, data_only=True)
        sheet = self._workbook.active

        if sheet is None:
            self.close()
            raise ValueError("В xlsx файле отсутствуют листы")

        # Параметр для расчёта прогресса
        self._total_rows = sheet.max_row if sheet.max_row else 100000
        self._processed_rows = 0

        self._rows_iterator = sheet.iter_rows(values_only=True)

        # Читаем и валидируем первую строку (заголовки)
        try:
            raw_headers = next(self._rows_iterator)
        except StopIteration:
            self.close()
            raise ValueError("Файл пуст или поврежден")

        if not raw_headers:
            self.close()
            raise ValueError("В файле отсутствует строка заголовков")

        # Приводим заголовки файла к нижнему регистру для надежного сравнения
        file_column_names = [str(h).strip().lower() for h in raw_headers if h is not None]

        if not set(self.column_names) <= set(file_column_names):
            self.close()
            raise ValueError(f"Неверная структура файла. Ожидались заголовки: {self.column_names}")

        # Создаем карту индексов колонок, чтобы не зависеть от их порядка в файле
        self._col_map = {name: file_column_names.index(name) for name in self.column_names}

        return self

    def __next__(self) -> dict[str, str]:
        if self._rows_iterator is None:
            raise StopIteration

        # Ищем следующую непустую строку
        while True:
            try:
                values = next(self._rows_iterator)
                self._processed_rows += 1
            except StopIteration:
                # Если строки кончились, гарантируем 100% прогресс и выходим
                self._total_rows = self._processed_rows
                self.close()
                raise StopIteration

            # Если строка содержит хоть какие-то данные — выходим из цикла поиска
            if values and any(v is not None for v in values):
                break

        result = {}
        for name in self.column_names:
            idx = self._col_map[name]
            # Если строка в файле оказалась короче, чем индекс нужной колонки
            val = values[idx] if idx < len(values) else None
            result[name] = str(val).strip() if val is not None else ''

        return result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
