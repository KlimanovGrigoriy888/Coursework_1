import json
from unittest.mock import patch

from src.views import for_main


def test_for_main_full_flow():
    # 1. Готовим фейковые данные, для подмены возврата функциями
    fake_range_data = {"start_data": "2021.10.01 00:00:00", "end_data": "2021.10.15 12:00:00"}
    fake_mock_report_agg = {
        'cards': [{'last_digits': '1234', 'total_spent': 300.0, 'cashback': 3.0}],
        'top_transactions': [
            {'date': '05.10.2021', 'amount': 200.0, 'category': 'Одежда', 'description': 'Zara'},
            {'date': '01.10.2021', 'amount': 100.0, 'category': 'Еда', 'description': 'Магнит'}]}
    fake_api_data = {
        "USD/RUB": {"price": "90.50"},
        "AAPL": {"price": "180.20"}
    }

    # 2. Патчим функции в модуле views (в src.views)
    with patch('src.views.get_range_data') as mock_range, \
            patch('src.views.read_excel_to_df') as mock_read, \
            patch('src.views.cart_agg_for_main') as mock_agg, \
            patch('src.views.get_currency_and_stocks') as mock_api, \
            patch('src.views.time_of_day') as mock_time:
        # Подставляем фейковые данные для возврата функциями
        mock_range.return_value = fake_range_data
        mock_read.return_value = "fake_dataframe"  # для теста неважно, что там внутри
        mock_agg.return_value = fake_mock_report_agg
        mock_api.return_value = (True, fake_api_data)
        mock_time.return_value = "Добрый день"

        # 3. Вызываем главную функцию
        result_json = for_main("2021-10-15 12:00:00")
        result = json.loads(result_json)  # Превращаем строку обратно в словарь для проверки

        # 4. Проверяем сборку финального JSON
        assert result == {'greeting': 'Добрый день',
                          'cards': [{'last_digits': '1234', 'total_spent': 300.0, 'cashback': 3.0}],
                          'top_transactions': [{'amount': 200.0,
                                                'category': 'Одежда',
                                                'date': '05.10.2021',
                                                'description': 'Zara'},
                                               {'amount': 100.0,
                                                'category': 'Еда',
                                                'date': '01.10.2021',
                                                'description': 'Магнит'}],
                          'currency_rates': [{'currency': 'USD', 'rate': 90.5}],
                          'stock_prices': [{'price': 180.2, 'stock': 'AAPL'}]
                          }
        assert result["greeting"] == "Добрый день"
        assert result["currency_rates"][0] == {"currency": "USD", "rate": 90.5}
        assert result["stock_prices"][0] == {"stock": "AAPL", "price": 180.2}
        assert len(result["cards"]) == 1

        # Проверяем, что функции вызывались правильно один раз с входным аргументом
        mock_range.assert_called_once_with("2021-10-15 12:00:00")
