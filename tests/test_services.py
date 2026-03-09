import json

from src.services import cashback_benefit, investment_bank


def test_cashback_benefit_with_empty_cashback():
    test_data = [
        {
            "Дата операции": "31.12.2021 16:44:00",
            "Категория": "Супермаркеты",
            "Кэшбэк": "3,50"
        },
        {
            "Дата операции": "31.12.2021 16:42:04",
            "Категория": "Супермаркеты",
            "Кэшбэк": ""  # Пустое значение должно стать 0
        },
        {
            "Дата операции": "31.12.2020 10:00:00",  # Другой год
            "Категория": "Одежда",
            "Кэшбэк": "10,00"
        }
    ]

    response = cashback_benefit(test_data, "2021", "12")
    result = json.loads(response)
    assert result["Супермаркеты"] == 3  # int(3.50 + 0)
    assert "Одежда" not in result


def test_investment_bank_with_empty_sum_opertations():
    test_data = [
        {
            "Дата операции": "31.12.2021 16:44:00",
            "Сумма операции": -1712.0
        },
        {
            "Дата операции": "31.12.2021 16:42:04",
            'Сумма операции': 0
        }
    ]
    response = investment_bank("2021-12", test_data, 50)
    assert response == 38.0