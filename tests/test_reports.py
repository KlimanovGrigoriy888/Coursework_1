import pandas as pd

from src.reports import get_range_data_for_reports, spending_by_category, spending_by_weekday
import datetime
import pytest


# ///////////////////////// Проверка функции get_range_data_for_reports() ////////////////////////////////
def test_get_range_data_for_reports():
    """Проверка когда дата корректна"""
    assert get_range_data_for_reports("28.05.2025 15:29:44") == (datetime.datetime(2025, 2, 27, 15, 29, 44),
                                                                 datetime.datetime(2025, 5, 28, 15, 29, 44))


def test_get_range_data_none():
    """Проверка работы без аргументов (текущее время)"""
    # Фиксируем время до запуска, чтобы избежать расхождения в миллисекундах
    now = datetime.datetime.now()
    start, end = get_range_data_for_reports(None)

    # Проверяем, что разница между 'now' и 'end' меньше секунды
    assert (end - now).seconds < 1
    assert (end - start).days == 90


@pytest.mark.parametrize("invalid_input", [
    "2024-05-20",  # Неверный формат
    "not a date",  # Не дата
    12345  # Не строка (попадет в блок else или вызовет ошибку в оригинале)
])
def test_get_range_data_fallback(invalid_input):
    """Проверка: если ввод даты неверный, берется текущая дата"""
    now = datetime.datetime.now()
    start, end = get_range_data_for_reports(invalid_input)

    # Если входные данные некорректны, функция должна вернуть datetime.now()
    assert (end - now).total_seconds() < 1


def test_get_range_data_as_datetime_object():
    """Проверка: если на вход подан уже объект datetime"""
    input_obj = datetime.datetime(2023, 1, 1, 12, 0, 0)
    start, end = get_range_data_for_reports(input_obj)

    assert end == input_obj
    assert (end - start).days == 90


# ///////////////////////// Проверка функции spending_by_category() ////////////////////////////////
@pytest.fixture
def transactions_df():
    transactions_dict = {"Дата операции": ["24.12.2021 16:44:00",
                                           "25.12.2021 16:42:04",
                                           "26.12.2021 16:39:04",
                                           "27.12.2021 15:44:39",
                                           "28.12.2021 01:23:42",
                                           "29.12.2021 01:23:42",
                                           "30.12.2021 01:23:42",
                                           "31.12.2021 01:23:42"],
                         "Сумма платежа": [
                             "-160,89", "-64,00", "-118,12", "-78,05",
                             "-564,00", "-800,00", "-20000,00", "-500,00"
                         ],
                         "Категория": ["Супермаркеты",
                                       "Различные товары",
                                       "Переводы",
                                       "Каршеринг",
                                       "Ж/д билеты",
                                       "Фастфуд",
                                       "Одежда и обувь",
                                       "Рестораны"
                                       ]}

    return pd.DataFrame(transactions_dict)


def test_spending_by_category_date_out_range(transactions_df):
    # Проверка: дата вне диапазона должна вернуть пустой Series и результат (сумма 0.0)
    result = spending_by_category(transactions_df, "Фастфуд", "01.12.2021 16:44:00")
    assert result.sum() == 0.0


def test_spending_by_category_only_negative():
    # Проверка: доходы (+500) должны игнорироваться, а расходы (-800) учитываться
    data = pd.DataFrame({
        "Дата операции": ["29.12.2021 10:00:00", "29.12.2021 10:00:00"],
        "Сумма платежа": ["500,00", "-800,00"],
        "Категория": ["Фастфуд", "Фастфуд"]
    })
    result = spending_by_category(data, "Фастфуд", "29.12.2021 23:59:59")
    assert result.sum() == 800.0



def test_spending_by_category_dirty_data():
    # Проверка: на наличие NaN и пробелов в названиях категорий
    data = pd.DataFrame({
        "Дата операции": ["29.12.2021 10:00:00", "29.12.2021 11:00:00"],
        "Сумма платежа": ["-100,00", "-200,00"],
        "Категория": [None, "  Фастфуд  "]
    })
    result = spending_by_category(data, "Фастфуд", "29.12.2021 23:59:59")
    assert result.sum() == 200.0


def test_spending_by_category_empty_df():
    # Проверка: при пустых входных данных получаем 0.0 без ошибок
    empty_df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория"])
    result = spending_by_category(empty_df, "Фастфуд", "29.12.2021 01:23:42")
    assert result.sum() == 0.0


def test_spending_by_category_missing_category(transactions_df):
    # Проверка: если категории нет в списке, сумма 0.0
    result = spending_by_category(transactions_df, "Несуществующая", "29.12.2021 01:23:42")
    assert result.sum() == 0.0


# ///////////////////////// Проверка функции spending_by_weekday() ////////////////////////////////
@pytest.fixture
def transactions_df_by_weekday():
    transactions_dict = {"Дата операции": ["20.12.2021 16:44:00",
                                           "20.12.2021 16:42:04",
                                           "21.12.2021 16:39:04",
                                           "21.12.2021 15:44:39",
                                           "25.12.2021 01:23:42",
                                           "25.12.2021 01:23:42",
                                           "26.12.2021 01:23:42",
                                           "26.12.2021 01:23:42"],
                         "Сумма платежа": [
                             "-160,89", "-64,00", "-118,12", "-78,05",
                             "-564,00", "-800,00", "-20000,00", "-500,00"
                         ],
                         "Категория": ["Супермаркеты",
                                       "Супермаркеты",
                                       "Каршеринг",
                                       "Каршеринг",
                                       "Фастфуд",
                                       "Фастфуд",
                                       "Рестораны",
                                       "Рестораны"
                                       ]}

    return pd.DataFrame(transactions_dict)


def test_spending_by_weekday(transactions_df_by_weekday):
    # Проверка когда функция принимает датафрейм и данные для поиска с положительным результатом поиска
    result = spending_by_weekday(transactions_df_by_weekday, "1.01.2022 01:23:42")
    # Преобразуем результат в словарь для сравнения результата
    dict_result = result.to_dict()

    expected_result = {'week_dey': {0: 'Monday', 1: 'Saturday', 2: 'Sunday', 3: 'Tuesday'},
                       'Категория': {0: 'Супермаркеты', 1: 'Фастфуд', 2: 'Рестораны', 3: 'Каршеринг'},
                       'Средние траты': {0: 112.44, 1: 682.0, 2: 10250.0, 3: 98.08}}
    assert dict_result == expected_result


def test_spending_by_weekday_not_date(transactions_df_by_weekday):
    # Проверка когда даты нет и дата вне диапазона сегодня дата которой нет в датафрейме
    result = spending_by_weekday(transactions_df_by_weekday, "")
    # Преобразуем результат в словарь для сравнения результата
    dict_result = result.to_dict()

    expected_result = {'week_dey': {}, 'Категория': {}, 'Средние траты': {}}
    assert dict_result == expected_result


def test_spending_by_weekday_date_out_range(transactions_df_by_weekday):
    # Проверка поиска трат при вводе даты вне диапазона дат в датафрейме
    result = spending_by_weekday(transactions_df_by_weekday, "20.12.2025 16:44:00")
    # Преобразуем результат в словарь для сравнения результата
    dict_result = result.to_dict()

    expected_result = {'week_dey': {}, 'Категория': {}, 'Средние траты': {}}
    assert dict_result == expected_result

def test_spending_by_weekday_bad_date(transactions_df_by_weekday):
    # Проверка на ввод неправильной даты
    result = spending_by_weekday(transactions_df_by_weekday, 64555656)
    # Преобразуем результат в словарь для сравнения результата
    dict_result = result.to_dict()

    expected_result = {'week_dey': {}, 'Категория': {}, 'Средние траты': {}}
    assert dict_result == expected_result


def test_spending_by_weekday_empty_df():
    # Проверка на пустой датафрейм
    empty_df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория"])
    result = spending_by_weekday(empty_df, "29.12.2021 01:23:42")
    # Преобразуем результат в словарь для сравнения результата
    dict_result = result.to_dict()

    expected_result = {'week_dey': {}, 'Категория': {}, 'Средние траты': {}}
    assert dict_result == expected_result
