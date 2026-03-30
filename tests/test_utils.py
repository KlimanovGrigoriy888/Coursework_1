from unittest.mock import patch, mock_open
import pytest
from datetime import datetime

from src.utils import time_of_day, read_excel_to_df, read_json_file, transformed_date, get_range_data, clean_amount, \
    settings_for_api, get_currency_and_stocks, cart_agg_for_main, read_excel
import pandas as pd
import json


@pytest.mark.parametrize("hour, expected", [
    (7, "«Доброе утро»"),
    (13, "«Добрый день»"),
    (19, "«Добрый вечер»"),
    (2, "«Доброй ночи»"),
    (23, "«Доброй ночи»"),
])
def test_time_of_day_parametrized(hour, expected):
    with patch('src.utils.dt') as mock_dt:
        mock_dt.now.return_value.time.return_value.hour = hour
        assert time_of_day() == expected


def test_time_of_day_except():
    with patch('src.utils.dt') as mock_dt:
        # Заменяем Exception c помощью лексики side_effect
        mock_dt.now.side_effect = Exception("Сбой системы")
        result = time_of_day()
        assert result == "Ошибка обработки даты Сбой системы"


def test_read_excel_to_df_file_not_found():
    # Тест случая, когда файла не существует
    # Патчим проверку пути, чтобы она вернула False
    with patch('src.utils.os.path.exists') as mock_exists:
        mock_exists.return_value = False

        result = read_excel_to_df("non_existent.xlsx")

        assert result == [{}]
        mock_exists.assert_called_once_with("non_existent.xlsx")


def test_read_excel_to_df_empty_path():
    # Тест пустого пути
    result = read_excel_to_df("")
    assert result == [{}]


def test_read_excel_to_df_success_with_fillna():
    # Тест успешного чтения и замены NaN
    # 1. Создаем фейковый DF, где есть NaN (пустая ячейка)
    mock_df = pd.DataFrame({
        'Amount': [100.0, None],
        'Category': ['Food', None]
    })

    # 2. Патчим и проверку пути, и само чтение
    with patch('src.utils.os.path.exists') as mock_exists, \
            patch('src.utils.pd.read_excel') as mock_read:
        mock_exists.return_value = True
        mock_read.return_value = mock_df

        result = read_excel_to_df("real_file.xlsx")

        # 3. Проверяем, что NaN превратились в пустые строки
        assert result.iloc[1]['Amount'] == ""
        assert result.iloc[1]['Category'] == ""
        assert result.shape == (2, 2)


@pytest.mark.parametrize("invalid_path", [None, ""])
def test_read_excel_invalid_paths(invalid_path):
    # Тест с двумя пустыми путями к файлу
    assert read_excel_to_df(invalid_path) == [{}]


def test_read_excel_not_found_file():
    # Патчим проверку отсутствия наличия пути
    with patch('src.utils.os.path.exists') as mock_exists:
        mock_exists.return_value = False
        result = read_excel("fake_file.xlsx")
        assert result == [dict()]


def test_read_excel_empty_path():
    # Проверка отсутствия названия файла
    result = read_excel("")
    assert result == [dict()]


def test_read_excel_success():
    # Создаем фейковый DF
    mock_df = pd.DataFrame({
        'Дата операции': [ '31.12.2021 16:44:00', '31.12.2021 16:42:04'],
        'Номер карты': ['*7197', None],
        'Сумма операции': [-160.89, None],
        'Категория': ['Супермаркеты', None],
        'Amount': [100.0, None],
        'Category': ['Food', None],

    })

    # Патчим проверку наличия пути и получение Dataframe
    with patch('src.utils.os.path.exists') as mock_exists, \
        patch('src.utils.pd.read_excel') as mock_read:
        mock_exists.return_value = True
        mock_read.return_value = mock_df
        # Подсовываем пустышку в качестве пути к файлу
        result = read_excel("fake_file.xlsx")
        print(result)
        # Проверка тестирования
        assert result[0]['Дата операции'] == '31.12.2021 16:44:00'
        assert result[0]['Номер карты'] == '*7197'
        assert result[1]['Номер карты'] == ''
        assert len(result) == 2


def test_read_json_file_empty_path():
    # Тест пустого пути
    result = read_json_file("")
    assert result == {}


@pytest.fixture
def data_json():
    return {
        "user_currencies": [
            "USD",
            "EUR"
        ],
        "user_stocks": [
            "AAPL",
            "AMZN",
            "GOOGL",
            "MSFT",
            "TSLA"
        ]
    }

def test_read_json_file_success(data_json):
    # 1. Используем mock_open для имитации открытия файла
    # 2. Патчим json.load, чтобы он вернул наш словарь из фикстуры
    with patch("builtins.open", mock_open(read_data="{}")), \
            patch("src.utils.json.load") as mock_json_load:
        mock_json_load.return_value = data_json

        result = read_json_file("test.json")

        # Проверяем конкретные данные
        assert result["user_currencies"] == ["USD", "EUR"]
        assert "AAPL" in result["user_stocks"]
        mock_json_load.assert_called_once()


def test_read_json_file_decode_error():
    # 1. Используем mock_open для имитации открытия файла
    # 2. Настраиваем json.load так, чтобы он ВЫБРОСИЛ ошибку декодирования
    with patch("builtins.open", mock_open(read_data="invalid json")), \
            patch("src.utils.json.load") as mock_json:
        # Имитируем ошибку JSONDecodeError
        # (Она требует аргументов для инициализации: сообщение, текст, позиция)
        mock_json.side_effect = json.JSONDecodeError("Expecting property name", "", 0)

        # 3. Вызываем функцию
        result = read_json_file("bad_format.json")

        # 4. Проверяем, что функция не "упала", а вернула пустой словарь из блока except
        assert result == {}


def test_read_json_file_not_path():
    # 1. Используем mock_open для имитации открытия файла
    # 2. Настраиваем json.load так, чтобы он ВЫБРОСИЛ ошибку декодирования
    with patch("builtins.open", mock_open(read_data="invalid json")), \
            patch("src.utils.json.load") as mock_json:
        # Имитируем ошибку FileNotFoundError
        mock_json.side_effect = FileNotFoundError()

        # 3. Вызываем функцию
        result = read_json_file("not path to json file")

        # 4. Проверяем, что функция не "упала", а вернула пустой словарь из блока except
        assert result == {}


def test_read_json_file_bad_type():
    # 1. Используем mock_open для имитации открытия файла
    # 2. Настраиваем json.load так, чтобы он ВЫБРОСИЛ ошибку декодирования
    with patch("builtins.open", mock_open(read_data="invalid json")), \
            patch("src.utils.json.load") as mock_json:
        # Имитируем ошибку TypeError
        mock_json.side_effect = TypeError()

        # 3. Вызываем функцию
        result = read_json_file("bad type in file")

        # 4. Проверяем, что функция не "упала", а вернула пустой словарь из блока except
        assert result == {}


def test_read_json_file_bad_value():
    # 1. Используем mock_open для имитации открытия файла
    # 2. Настраиваем json.load так, чтобы он ВЫБРОСИЛ ошибку декодирования
    with patch("builtins.open", mock_open(read_data="invalid json")), \
            patch("src.utils.json.load") as mock_json:
        # Имитируем ошибку ValueError
        mock_json.side_effect = ValueError()

        # 3. Вызываем функцию
        result = read_json_file("bad type in file")

        # 4. Проверяем, что функция не "упала", а вернула пустой словарь из блока except
        assert result == {}


@pytest.mark.parametrize("input_data, expected", [("31.12.2021 16:44:00", "2021.12.31 16:44:00"),
                                                  ("2021.12.21 16:44:00", None),
                                                  (datetime(year=2021, month=12, day=31, hour=16, minute=44, second=20),
                                                   "2021.12.31 16:44:20"),
                                                  ("", None),
                                                  (45555, None)])
def test_transformed_date(input_data, expected):
    # Тесты на возможные случаи принятия даты
    result = transformed_date(input_data)
    assert result == expected


@pytest.mark.parametrize("input_data, expected_range_data", [
    ("2024-03-11 14:26:55", {'start_data': '2024.03.01 00:00:00', 'end_data': '2024.03.11 14:26:55'}),
    ("12.21.2021 16:44:00", None),
    ("", None),
    (45555, None)])
def test_get_range_data(input_data, expected_range_data):
    # Тесты функции на возможные случаи принятия даты
    result = get_range_data(input_data)
    assert result == expected_range_data


@pytest.mark.parametrize("input_value, expected_value", [
    (" 0,55 ", 0.55),
    ("1.00", 1.00),
    ("", 0.0),
    (45555, 45555.0)])
def test_clean_amount(input_value, expected_value):
    # Тесты функции на возможные случаи принятия данных
    result = clean_amount(input_value)
    assert result == expected_value


def test_settings_for_api():
    # Подготовка данных, которые якобы вернул read_json_file
    mock_json_content = {'user_currencies': ['USD', 'EUR'],
                         'user_stocks': ['AAPL', 'AMZN']}

    # Патчим внутреннюю функцию read_json_file
    with patch('src.utils.read_json_file') as mock_read:
        mock_read.return_value = mock_json_content

        # Вызываме тестируемую функцию
        result = settings_for_api("fake_path.json")

        # Проверяем как отработала функция
        expected_result = "AAPL,AMZN,USD/RUB,EUR/RUB"
        assert result == expected_result
        mock_read.assert_called_once_with("fake_path.json")


def test_settings_for_api_empty_path():
    # Проверка на пустой путь
    assert settings_for_api("") == ""


def test_settings_for_api_part_data():
    mock_data = {"user_stocks": ["AAPL"]}
    # Проверка на неполные данные в json файле
    with patch('src.utils.read_json_file') as mock_read:
        mock_read.return_value = mock_data
        # Проверяем как отработала функция с неполными данными
        assert settings_for_api("path.json") == "AAPL"


def test_settings_for_api_not_data_from_json():
    mock_data = {}
    # Проверка на неполные данные в json файле
    with patch('src.utils.read_json_file') as mock_read:
        mock_read.return_value = mock_data
        # Проверяем как отработала функция с неполными данными
        assert settings_for_api("path.json") == ""


def test_get_currency_and_stocks():
    mock_getting_data = {'AAPL': {'price': '248.62000'}, 'AMZN': {'price': '199.3'},
                         'USD/RUB': {'price': '81.47078'},
                         'EUR/RUB': {'price': '93.9486'}}

    with patch('src.utils.settings_for_api') as mock_settings, \
            patch('src.utils.requests.get') as mock_get:
        # Патчим возвращение данных из настроек запрос из json файла
        mock_settings.return_value = "AAPL,AMZN,USD/RUB,EUR/RUB"
        # Патчим ответ от сервера
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_getting_data

        status, data = get_currency_and_stocks()

        # Проверка на соответствие запроса ответу
        assert data == {'AAPL': {'price': '248.62000'}, 'AMZN': {'price': '199.3'},
                         'USD/RUB': {'price': '81.47078'},
                         'EUR/RUB': {'price': '93.9486'}}
        assert status is True
        assert data['AAPL'] == {'price': '248.62000'}


def test_get_currency_and_stocks_server_error():
    """Тест при получении кода ошибки сервера (например, 404 или 500)"""
    with patch('src.utils.requests.get') as mock_get:
        mock_get.return_value.status_code = 404
        mock_get.json.return_value = {"Example - message": "Not Found"}

        success, data = get_currency_and_stocks()

        assert success is False
        assert data == {}


def test_get_currency_and_stocks_exception():
    """Тест сетевой ошибки соединения интернета (таймаут или отсутствие интернета)"""
    with patch('src.utils.requests.get') as mock_get:
        # Имитируем Exception при попытке достучаться до сервера
        mock_get.side_effect = Exception("Example - Connection Error")

        success, data = get_currency_and_stocks()

        assert success is False
        assert data == {}


@pytest.fixture
def test_df():
    return pd.DataFrame({
        "Номер карты": ["*1234", "*1234", "*5678", None, ""],
        "Дата операции": ["01.10.2023 10:00:00", "05.10.2023 12:00:00", "15.10.2023 15:00:00", "01.10.2023 00:00:00",
                          "01.10.2023 00:00:00"],
        "Сумма операции с округлением": ["100,00", "200,00", "5000,00", "100", "100"],
        "Сумма операции": ["100,00", "200,00", "5000,00", "100", "100"],
        "Категория": ["Еда", "Одежда", "Техника", "Прочее", "Прочее"],
        "Описание": ["Магнит", "Zara", "re:Store", "Ошибка", "Ошибка"]
    })

def test_cart_agg_for_main(test_df):
    # Задаем диапазон дат
    start = "2023.10.01 00:00:00"
    stop = "2023.10.10 23:59:59"

    # Патчим time_of_day, чтобы приветствие было запатчено
    with patch('src.utils.time_of_day') as mock_time:
        mock_time.return_value = "«Добрый день»"

        result = cart_agg_for_main(test_df, start, stop)

        # Проверяем приветствие
        assert result['greeting'] == '«Добрый день»'
        # Проверяю весь ответ
        assert result == {'greeting': '«Добрый день»',
                          'cards': [{'last_digits': '1234', 'total_spent': 300.0, 'cashback': 3.0}],
                          'top_transactions': [
                              {'date': '05.10.2023', 'amount': 200.0, 'category': 'Одежда', 'description': 'Zara'},
                              {'date': '01.10.2023', 'amount': 100.0, 'category': 'Еда', 'description': 'Магнит'}]}

        # Проверяем карты (в фильтр должны попасть только две операции по карте *1234)
        # Карта *5678 не должна попасть, так как её дата 15.10 вне диапазона до 10.10
        assert len(result["cards"]) == 1
        card_info = result["cards"][0]
        assert card_info["last_digits"] == "1234"
        assert card_info["total_spent"] == 300.0  # 100 + 200
        assert card_info["cashback"] == 3.0       # 300 / 100

        # Проверяем топ транзакций (только те, что прошли фильтр по дате)
        assert len(result["top_transactions"]) == 2
        # Первая в топе должна быть самая крупная (200.0)
        assert result["top_transactions"][0]["amount"] == 200.0
        assert result["top_transactions"][0]["date"] == "05.10.2023"

