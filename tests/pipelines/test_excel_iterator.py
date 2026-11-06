import io
import openpyxl
import pytest
from django.core.files.base import ContentFile
from gge_marketplace.pipelines.infrastructure.xlsx_reader import XlsxIterator


@pytest.fixture
def create_xlsx_file():
    """Фикстура для генерации Excel-файла в памяти с поддержкой read_only=True."""

    def _generate(headers: list, rows: list[list]) -> ContentFile:
        wb = openpyxl.Workbook()
        ws = wb.active

        if headers:
            ws.append(headers)
        for row in rows:
            ws.append(row)

        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)

        django_file = ContentFile(file_stream.read(), name="test_file.xlsx")
        return django_file

    return _generate


def test_iterator_success(create_xlsx_file):
    """Проверка успешного чтения корректного файла."""
    headers = ['order_id', 'user_email', 'sku', 'quantity', 'price_on_buy']
    rows = [
        ['123', 'test@user.com', 'SKU-A', '2', '150.0'],
        ['124', 'test2@user.com', 'SKU-B', '1', '300.5']
    ]
    fake_file = create_xlsx_file(headers, rows)
    expected_headers = ['order_id', 'user_email', 'sku', 'quantity', 'price_on_buy']

    # Проверяем работу контекстного менеджера и итератора
    with XlsxIterator(fake_file, expected_headers) as xslt_iterator:
        result = list(xslt_iterator)

    assert len(result) == 2
    assert result[0]['order_id'] == '123'
    assert result[0]['sku'] == 'SKU-A'
    assert result[1]['user_email'] == 'test2@user.com'


def test_iterator_ignores_empty_rows(create_xlsx_file):
    """Итератор должен пропускать полностью пустые строки (состоящие из None)."""
    headers = ['sku', 'quantity']
    rows = [
        ['SKU-A', '2'],
        [None, None],  # Полностью пустая строка
        ['SKU-B', '1']
    ]
    fake_file = create_xlsx_file(headers, rows)

    with XlsxIterator(fake_file, ['sku', 'quantity']) as xslt_iterator:
        result = list(xslt_iterator)

    assert len(result) == 2  # Пустая строка проигнорирована
    assert result[0]['sku'] == 'SKU-A'
    assert result[1]['sku'] == 'SKU-B'


def test_iterator_handles_short_rows_and_none(create_xlsx_file):
    """Проверка защиты от IndexError (короткие строки) и превращения None в пустую строку."""
    headers = ['sku', 'quantity', 'price_on_buy']
    rows = [
        ['SKU-A', '2'],  # Строка короче, чем список заголовков (нет цены)
        ['SKU-B', None, '100']  # Явный None в ячейке
    ]
    fake_file = create_xlsx_file(headers, rows)

    with XlsxIterator(fake_file, ['sku', 'quantity', 'price_on_buy']) as xslt_iterator:
        result = list(xslt_iterator)

    assert len(result) == 2
    # В короткой строке отсутствующий элемент стал пустой строкой
    assert result[0]['price_on_buy'] == ''
    # Явный None тоже превратился в пустую строку и очистился от пробелов
    assert result[1]['quantity'] == ''


def test_iterator_progress_calculation(create_xlsx_file):
    """Проверка корректности расчета прогресса."""
    headers = ['sku']
    rows = [['A'], ['B'], ['C'], ['D']]  # 4 строки данных + 1 строка заголовков = 5 строк всего
    fake_file = create_xlsx_file(headers, rows)

    with XlsxIterator(fake_file, ['sku']) as xslt_iterator:
        iterator = iter(xslt_iterator)

        assert iterator.progress == (1 / 5)

        next(iterator)  # Читаем 1-ю строку данных
        # Обработано: 1 строка заголовков + 1 строка данных = 2 строки из 5
        assert iterator.progress == (2 / 5)

        next(iterator)
        next(iterator)
        next(iterator)

        with pytest.raises(StopIteration):
            next(iterator)

        # В конце гарантируем 100%
        assert iterator.progress == 1


def test_iterator_raises_error_if_file_empty(create_xlsx_file):
    """Файл вообще без строк должен выбрасывать ValueError."""
    fake_file = create_xlsx_file(headers=[], rows=[])

    with pytest.raises(ValueError, match="Файл пуст или поврежден"):
        with XlsxIterator(fake_file, ['sku']) as xslt_iterator:
            list(xslt_iterator)


def test_iterator_raises_error_if_headers_missing(create_xlsx_file):
    """Если в файле неверная структура заголовков, должна быть ошибка."""
    headers = ['wrong_header_1', 'wrong_header_2']
    rows = [['val1', 'val2']]
    fake_file = create_xlsx_file(headers, rows)

    with pytest.raises(ValueError, match="Неверная структура файла. Ожидались заголовки"):
        with XlsxIterator(fake_file, ['sku', 'quantity']) as xslt_iterator:
            list(xslt_iterator)


def test_iterator_closes_workbook_on_error(create_xlsx_file):
    """Книга openpyxl должна закрываться даже при возникновении ошибок валидации."""
    headers = ['wrong_headers']
    fake_file = create_xlsx_file(headers, [])

    xslt_iterator = XlsxIterator(fake_file, ['sku'])

    with pytest.raises(ValueError):
        with xslt_iterator:
            list(xslt_iterator)

    # Проверяем, что внутренний workbook сброшен в None (метод close сработал через контекст)
    assert xslt_iterator._workbook is None
