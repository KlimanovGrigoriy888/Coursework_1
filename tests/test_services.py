import json

import pytest

from src.services import cashback_benefit, investment_bank, simple_search, search_with_phone_number


def test_cashback_benefit():
    # Проверка на стандартный поиск, включающий пустые значения Кэшбэк
    test_data = [
        {"Дата операции": "31.12.2021 16:44:00", "Категория": "Одежда и обувь", "Кэшбэк": ""},
        {"Дата операции": "31.12.2021 16:44:00", "Категория": "Супермаркеты", "Кэшбэк": "3,50"},
        {
            "Дата операции": "31.12.2021 16:42:04",
            "Категория": "Супермаркеты",
            "Кэшбэк": "",  # Пустое значение должно стать 0
        },
        {"Дата операции": "31.12.2020 10:00:00", "Категория": "Одежда", "Кэшбэк": "10,00"},  # Другой год
    ]

    response = cashback_benefit(test_data, "2021", "12")
    print(response)
    result = json.loads(response)
    assert result["Супермаркеты"] == 3  # int(3.50 + 0)
    assert "Одежда" not in result


def test_cashback_benefit_do_not_found():
    # Проверка на отсутствие найденной даты
    test_data = [
        # Некорректный формат даты
        {"Дата операции": 1222, "5646341": "Супермаркеты", "Кэшбэк": "3,50"},
        # Некорректный формат даты
        {"Дата операции": "2021-12-31", "Категория": "Кино", "Кэшбэк": "100"},
        # Некорректный формат кэшбэка
        {"Дата операции": "31.12.2021 10:00:00", "Категория": "Аптеки", "Кэшбэк": "много"},
    ]
    response = cashback_benefit(test_data, 2021, 12)
    assert response == "{}"  # Ожидаем пустой словарь, так как данные битые


def test_investment_bank_with_empty_sum_operatations():
    test_data = [
        {"Дата операции": "31.12.2021 16:44:00", "Сумма операции": -1712.0},
        {"Дата операции": "31.12.2021 16:42:04", "Сумма операции": 0},
    ]
    response = investment_bank("2021-12", test_data, 50)
    assert response == 38.0


@pytest.fixture
def data_test_list():
    return [
        {
            "Дата операции": "23.01.2018 21:39:01",
            "Дата платежа": "24.01.2018",
            "Категория": "Переводы",
            "Описание": "Перевод Кредитная карта. ТП 10.2 RUR",
        },
        {
            "Дата операции": "20.07.2019 15:27:06",
            "Дата платежа": "23.07.2019",
            "Категория": "Наличные",
            "Описание": "Снятие в банкомате Сбербанк",
        }
    ]


def test_simple_search_find(data_test_list):
    # Проверка удачного поиска
    result = simple_search('Переводы', data_test_list)
    result_list = json.loads(result)

    assert len(result_list) == 1
    assert result_list[0]["Категория"] == "Переводы"


def test_simple_search_find_other_field(data_test_list):
    # Проверка наличия других данных в результате
    result = simple_search('Переводы', data_test_list)
    result_list = json.loads(result)

    assert len(result_list) == 1
    assert "Кредитная карта" in result_list[0]["Описание"]


def test_simple_search_not_search_data(data_test_list):
    # Когда нет данных поисковых данных
    transactions = data_test_list
    assert simple_search("", transactions) == '[]'


def test_simple_search_not_transactions():
    # Когда нет данных транзакций
    assert simple_search('Переводы', None) == '[]'


def test_simple_search_do_not_find(data_test_list):
    # Когда поиск ничего не нашел
    assert simple_search("Космос", data_test_list) == '[]'


@pytest.fixture
def data_test_list_with_phone_number():
    return [
        {"id": 1, "Описание" : "Я МТС +7 921 11-22-33"},
        {"id": 2, "Описание" : "Тинькофф Мобайл +7 995 555-55-55"},
        {"id": 3, "Описание": "Без номера"},
        {"id": 4, "Описание": "МТС Mobile +7 981 333-44-55"}
    ]


def test_search_with_phone_number(data_test_list_with_phone_number):
    # Получаем результат в json ответе
    result_json = search_with_phone_number(data_test_list_with_phone_number)
    # Преобразуем результат в ответ в виде списка
    result_list = json.loads(result_json)
    print(result_list)

    # Проверяем количество найденных транзакций
    found_id = [item["id"] for item in result_list]
    assert 1 in found_id
    assert 2 in found_id
    assert 4 in found_id

    assert len(result_list) == 3
    # Проверяем результат
    assert result_list[0]["Описание"] == "Я МТС +7 921 11-22-33"
