import json
import os
from typing import Any

from src.utils import cart_agg_for_main, get_currency_and_stocks, get_range_data, read_excel_to_df, time_of_day

PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")


def for_main(input_date_str: str) -> str:
    """Принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS,
    возвращает JSON-ответ в нужном формате"""
    try:
        # 1. Подготовка дат (от 1-го числа до user_date_str)
        date_range = get_range_data(input_date_str)

        # 2. Чтение файла через функцию read_excel_to_df
        df = read_excel_to_df(PATH_TO_FILE_EXCEL)

        # 3. Агрегация данных по картам и транзакциям
        report_data = cart_agg_for_main(df, date_range["start_data"], date_range["end_data"])

        # 4. Получение курсов валют и акций через API
        success, api_raw = get_currency_and_stocks()

        currency_rates = []
        stock_prices = []

        if success:
            # Распределяем данные API по спискам
            for symbol, info in api_raw.items():
                price = float(info.get("price", 0))
                if "/RUB" in symbol:
                    currency_rates.append(
                        {"currency": symbol.split("/")[0], "rate": round(price, 2)}  # Берем только код валюты (USD)
                    )
                else:
                    stock_prices.append({"stock": symbol, "price": round(price, 2)})

        # 5. Сборка финального JSON-ответа по вашему шаблону
        result = {
            "greeting": time_of_day(),
            "cards": report_data["cards"],
            "top_transactions": report_data["top_transactions"],
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }
        return json.dumps(result, ensure_ascii=False, indent=4)
    except Exception as e:
        # Возврат данных если возникло исключение
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def events(
    input_date_str: str,
) -> dict[list | Any]:
    pass


if __name__ == "__main__":
    print(for_main("2021-03-11 14:26:55"))
