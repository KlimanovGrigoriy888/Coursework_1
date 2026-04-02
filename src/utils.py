from asyncio import timeout
from datetime import datetime as dt
from json import JSONDecodeError
from typing import Any, List, Dict, Tuple
from dotenv import load_dotenv
import requests

import pandas as pd
import json
import os

from pandas import DataFrame

from src.logger import setup_logging

# Пути открытия json и excel файлов с данными.
PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")
PATH_TO_FILE_USER_SETTINGS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "user_settings.json")

# Данные для API запроса курса валют и ценах на акции
load_dotenv()
URL = os.getenv("BASE_URL_API")
API = os.getenv("API_KEY")

# Создаем логгеры.
logger_read_json = setup_logging("read_json")
logger_date_of_day = setup_logging("setup_logging")
logger_excel_to_df = setup_logging("read_excel_to_df")
logger_transformed_date = setup_logging("transformed_date")
logger_get_range_data = setup_logging("get_range_data")


def time_of_day() -> str:
    """Функция определяет текущее время и в зависимости от времени дня возвращает строку
     в виде «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»"""
    logger_date_of_day.info("Начало работы функции")
    try:
        time_now = dt.now().time()
        time_hours = time_now.hour
        if 6 <= time_hours < 12:
            logger_date_of_day.info("Функция вернула значение «Доброе утро»")
            return "«Доброе утро»"
        elif 12 <= time_hours < 18:
            logger_date_of_day.info("Функция вернула значение «Добрый день»")
            return "«Добрый день»"
        elif 18 <= time_hours < 22:
            logger_date_of_day.info("Функция вернула значение «Добрый вечер»")
            return "«Добрый вечер»"
        else:
            logger_date_of_day.info("Функция вернула значение «Доброй ночи»")
            return "«Доброй ночи»"
    except Exception as e:
        logger_date_of_day.error(f"Возникла ошибка обработки даты {e}")
        return f"Ошибка обработки даты {e}"


def read_json_file(path_to_file_json: str) -> dict[str, Any]:
    """ Принимает путь до .json файла и возвращает список словарей, используется в функции settings_for_api()
     для получения списка в JSON формате данных для запроса по API  """
    logger_read_json.info("Начало работы функции")
    if not path_to_file_json:
        logger_read_json.error("Функции не передали путь к файлу json")
        return {}
    try:
        logger_read_json.info(f"Открытие файла json")
        with open(path_to_file_json, "r") as file:
            data_json = json.load(file)
            logger_read_json.info("Функция возвращает словарь из json файла")
            return data_json
    except (FileNotFoundError, JSONDecodeError, TypeError, ValueError) as e:
        logger_read_json.error(f"Ошибка сериализации JSON: {e}, функция вернет пустой словарь")
        print("Reading json fault")
        return {}


# def write_json_format(data_list: Any) -> str:
#     """Принимает подготовленный формат списка словарей для преобразования в JSON-строку с обработкой исключений."""
#     if not data_list:
#         return "{}"
#     try:
#         # indent делает JSON читаемым, ensure_ascii=False сохраняет кириллицу
#         return json.dumps(data_list, indent=4, ensure_ascii=False)
#     except (TypeError, ValueError) as e:
#         logger_read_json.error(f"Ошибка сериализации JSON: {e}")
#         return "{}"


def read_excel(path_to_file_excel: str) -> list[dict[Any, Any]]:
    """Принимает путь до .xlsx файла финансовых операций, возвращает список словарей с транзакциями.
      """
    if not path_to_file_excel or not os.path.exists(path_to_file_excel):
        return [dict()]
    excel_data_df = pd.read_excel(path_to_file_excel)
    # Чистим датафрейм от NaN значений заменяя эти значения на пустую строку
    df_excel_data_replace_none = excel_data_df.astype(object).where(pd.notnull(excel_data_df), "")
    result_list_of_dict = df_excel_data_replace_none.to_dict(orient='records')
    return result_list_of_dict


def read_excel_to_df(path_to_file_excel: str) -> list[dict[Any, Any]] | DataFrame:
    """Принимает путь до .xlsx файла финансовых операций, возвращает финансовые операции в формате DataFram."""
    logger_excel_to_df.info("Начало работы функции")
    if not path_to_file_excel or not os.path.exists(path_to_file_excel):
        logger_excel_to_df.error("Функции не передали путь к файлу excel или путь к файлу несуществует")
        return [{}]
    df = pd.read_excel(path_to_file_excel)
    # Заменяем NaN на пустые строки напрямую
    logger_excel_to_df.info(f"Функция возвращает dataframe с обработкой пустых ячеек")
    return df.fillna("")


def transformed_date(first_str_date: str) -> str | None:
    """Принимает строку в формате DD.MM.YYYY HH:MM:SS и возвращает "YYYY.MM.DD HH:MM:SS"
     для корректного сравнения строк в DataFrame."""
    logger_transformed_date.info("Начало работы функции")
    # Если дата пустая или не строка — возвращаем Nonelogger
    try:
        # Если Pandas уже превратил ячейку в дату (объект)
        if hasattr(first_str_date, 'strftime'):
            logger_transformed_date.info("На входе функции формат datetime, преобразуем время в нужный формат строки")
            return first_str_date.strftime('%Y.%m.%d %H:%M:%S')
        # Если дата пустая или не строка — возвращаем None
        if isinstance(first_str_date, str):
            logger_transformed_date.info("На входе функции формат времени строка, преобразуем в нужный формат строки")
            valid_format_date = dt.strptime(first_str_date, '%d.%m.%Y %H:%M:%S')
            return valid_format_date.strftime('%Y.%m.%d %H:%M:%S')

        logger_transformed_date.error("На входе функции неверный формат данных, возвращаем None")
        return None
    except (ValueError, TypeError) as e:
        logger_transformed_date.error(f"Возникло исключение {e}, возвращаем None")
        return None


def get_range_data(first_str_date: str) -> dict[str, str] | None:
    """Принимает строку в формате YYYY-MM-DD HH:MM:SS возвращает диапазон: от начала месяца до указанной даты
    в формате YYYY.MM.DD HH:MM:SS" в виде словаря {"start_data": start_data, "end_data": end_data}."""
    logger_get_range_data.info("Начало работы функции")
    try:
        # Если дата пустая или не строка — возвращаем None
        if not isinstance(first_str_date, str):
            logger_get_range_data.error("На вход функции передали не строку формата времени или ничего не предали")
            return None
        logger_get_range_data.info("На вход функции передали строку формата времени, перевод в формат datatime")
        valid_date = dt.strptime(first_str_date, '%Y-%m-%d %H:%M:%S')
        # Конец периода
        logger_get_range_data.info("Возврат строки конца диапазона даты")
        end_data = valid_date.strftime('%Y.%m.%d %H:%M:%S')
        # Начало периода (заменяем день, час, минуту и секунду на начало месяца)
        start_data = valid_date.replace(day=1, hour=0, minute=0, second=0).strftime('%Y.%m.%d %H:%M:%S')

        logger_get_range_data.info("Возврат строки начала диапазона даты")
        result = {"start_data": start_data, "end_data": end_data}
        return result
    except ValueError as e:
        logger_get_range_data.info(f"Возникло исключение {e}, возбуждаем исключение ValueError")
        return None


def clean_amount(value: float | str) -> float:
    """Принимает строку с цифровым значение или цифры и очищает значение суммы: убирает запятые,
     лишние пробелы по краям и конвертирует во float."""
    try:
        cleaned = str(value).replace(',', '.').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def cart_agg_for_main(operations_df: pd.DataFrame, start_data: str, stop_data: str) -> dict[
    str, str | list[dict[str, float | Any]] | list[dict[str, float | Any]]]:
    """Принимает DataFrame с финансовыми операциями, даты начала и конца в виде строки и фильтрует по диапазону даты,
     производит агрегацию по каждому номеру карты и по каждой карте возвращает общую сумму расходов
      и кешбэк (1 рубль на каждые 100 рублей) и топ 5 транзакций по сумме платежа"""
    # 1. Работаем с копией и убираем пустые номера карт через .notnull()
    df = operations_df.copy()
    df = df[df["Номер карты"].notnull()]

    # Доп. очистка, убираем пробелы и пустые строки в номерах карт
    df["Номер карты"] = df["Номер карты"].astype(str).str.strip()
    df = df[df["Номер карты"] != ""]

    # 2. Подготовка числовых колонок и дат с использованием внешних функций clean_amount и transformed_date
    target_col = "Сумма операции с округлением"
    df[target_col] = df[target_col].map(clean_amount)
    df["Дата для фильтра"] = df["Дата операции"].map(transformed_date)

    # 3. Фильтрация по датам
    filtered_df = df[(df["Дата для фильтра"] >= start_data) & (df["Дата для фильтра"] <= stop_data)]

    # 4. Формирование списка карт
    cards_list = []
    # Перебор по 'Номер карты' как единица группы и сгруппированному датафрейму 'group' отнесенному к этой единице
    for card_number, group in filtered_df.groupby("Номер карты"):
        # В сгруппированном датафрейме номера карты производим подсчет суммы "Сумма операции с округлением"
        total = float(group[target_col].sum())  # Конвертация в обычный float "Сумма операции с округлением"
        # Добавляем в результирующий список номер карты ее посчитанную сумму "Сумма операции с округлением"
        # и посчитанный кэшбэк 1 рубль на каждые 100 рублей
        cards_list.append({
            "last_digits": card_number.replace('*', ''),
            "total_spent": round(total, 2),
            "cashback": round(total / 100, 2)
        })

    # 5. Топ-5 транзакций по всем картам периода получаем путем сортирования по убыванию
    top_5_raw = filtered_df.sort_values(target_col, ascending=False).head(5)
    top_transactions = []
    for index, row in top_5_raw.iterrows():
        top_transactions.append({
            "date": row["Дата операции"].split()[0],  # Берем только дату без времени
            "amount": float(clean_amount(row["Сумма операции"])),
            "category": row["Категория"],
            "description": row["Описание"]
        })

    # Сборка финального ответа
    return {
        "greeting": time_of_day(),  # Вызов вашей функции
        "cards": cards_list,
        "top_transactions": top_transactions
    }


def settings_for_api(path_to_settings_json: str) -> str:
    """Функция принимает путь до .json файла с установками для запроса по API, возвращает необходимую
     строку для API запроса по url адресу "https://api.twelvedata.com" в необходимом формате."""
    if not path_to_settings_json:
        return ""
    result_from_json = read_json_file(path_to_settings_json)
    # Если файл не прочитался или пустой — возвращаем пустую строку
    if not result_from_json:
        return ""

    # Используем .get() и указываем пустой список [] как значение по умолчанию
    currencies = result_from_json.get("user_currencies", [])
    stocks = result_from_json.get("user_stocks", [])

    result_currencies = [f"{currency}/RUB" for currency in currencies]

    # Складываем списки и объединяем в строку
    result_str_symbols = ",".join(stocks + result_currencies)
    return result_str_symbols


def get_currency_and_stocks() -> tuple[bool, dict[str, Any]]:
    """Функция обращается к внешнему API для получения текущего курса валют по отношению к рублю
     по заданному формату из файла user_settings.json, возвращает json данные о
     курсах акций и курсах валют"""

    # Преобразование данных запроса об акциях и валютах и из json файла в строку для url запроса.
    result_str_symbols = settings_for_api(PATH_TO_FILE_USER_SETTINGS)

    # Пример строки запроса валюты из файла user_settings.json symbols="AAPL,MSFT,USD/RUB,EUR/USD" в данном проекте
    url = f"{URL}/price?symbol={result_str_symbols}&apikey={API}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        status = response.status_code
        if status != 200:
            print(f"Ошибка API: {data.get('message')}")
            return False, {}
        return True, data
    except Exception as fault:
        print(f"Ошибка запроса: {fault}")
        return False, {}


# if __name__ == "__main__":
    # print(time_of_day())
    # print(transformed_date("31.12.2021 16:44:00"))
    # print(time_of_day())

    # df_data = read_excel_to_df(PATH_TO_FILE_EXCEL)
    # print(df_data.head().to_dict())
    # filtered_data = cart_agg_for_main(df_data, "2021.11.25 19:02:06", "2021.11.29 18:09:38")
    # print(filtered_data)

    # print(get_date("29.12.2021 22:32:24"))
    # print(get_range_data("2024-03-11 14:26:55"))
    # result_from_json = read_json_file(PATH_TO_FILE_USER_SETTINGS)
    # print(result_from_json)
    # result_settings = settings_for_api(PATH_TO_FILE_USER_SETTINGS)
    # print(result_settings)
    # result_from_api = get_currency_and_stocks()
    # print(result_from_api)
