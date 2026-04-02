import json
import os
import re
from datetime import datetime
from typing import Any

from src.logger import setup_logging
from src.utils import read_excel

PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")
data = read_excel(PATH_TO_FILE_EXCEL)

logger_cashback_benefit = setup_logging("cashback_benefit")
logger_investment_bank = setup_logging("investment_bank")
logger_simple_search = setup_logging("simple_search")
logger_search_with_phone_number = setup_logging("search_with_phone_number")

def cashback_benefit(data_list: list[dict[str, Any]], year: int, month: int) -> str:
    """
    Функция принимает на вход список словарей с транзакциями, анализирует список транзакций и подсчитывает потенциальный
     кешбэк по категориям за указанный год и месяц, принимает на вход data - данные с транзакциями, year — год и
     month — месяц, за который проводится анализ. Возвращает JSON с анализом, сколько на каждой
      категории можно заработать кешбэка.
    """
    logger_cashback_benefit.info(f"Начало анализа кэшбэка за {month}.{year}")

    # Результирующий словарь: {Категория: Сумма кэшбэка}
    category_cashback = {}

    # Приводим входные фильтры к числам для сравнения
    target_year = int(year)
    target_month = int(month)

    for transaction in data_list:
        try:
            # 1. Извлекаем данные даты из списка транзакций
            date_str = transaction.get("Дата операции")
            if not date_str:
                continue
            # Преобразуем полученные данные даты в объект datatime
            dt_obj = datetime.strptime(str(date_str), "%d.%m.%Y %H:%M:%S")

            # 2. Проверяем по условию соответствия входному году и месяцу
            if dt_obj.year == target_year and dt_obj.month == target_month:
                category = transaction.get("Категория", "Неизвестно")

                # 3. Получение значения кэшбэка
                # Если в данных пустая строка или None — используем "0"
                raw_cashback = transaction.get("Кэшбэк")
                if not raw_cashback or str(raw_cashback).strip() == "":
                    cashback_val = 0.0
                else:
                    # Заменяем запятую на точку для конвертации во float
                    cashback_val = float(str(raw_cashback).replace(',', '.'))

                # 4. Аккумуляция суммы
                category_cashback[category] = category_cashback.get(category, 0.0) + cashback_val

        except (ValueError, TypeError) as e:
            logger_cashback_benefit.error(f"Ошибка при обработке строки: {e}")
            continue

    # Округляем итоговые суммы до целого числа
    result = {category: int(total_sum) for category, total_sum in category_cashback.items()}

    logger_cashback_benefit.info("Анализ завершен успешно")
    return json.dumps(result, ensure_ascii=False, indent=4)


def investment_bank(month: str, transactions: list[dict[str, Any]], limit: int) -> float :
    """Функция, принимает на вход:
     month — месяц в формате 'YYYY-MM', для которого рассчитывается отложенная сумма.
     transactions — список словарей, содержащий информацию о транзакциях, в которых содержатся следующие поля.
     limit — предел, до которого нужно округлять суммы операций (целое число).
     Возвращает сумму, которую удалось бы отложить в «Инвесткопилку»."""

    logger_investment_bank.info(f"Начало анализа кэшбэка за {month} c лимитом {limit}")

    # Сумма "инвесткопилки": Сумма
    amount_investment_bank = 0

    # Защита от деления на ноль
    if limit <= 0:
        return 0.0

    for transaction in transactions:
        try:
            #  Извлекаем данные даты из списка транзакций
            date_str = transaction.get("Дата операции")
            # Пропускаем операции в которых нет даты
            if not date_str:
                continue
            # Преобразуем полученные данные даты в объект datatime и пропускаем ненужные месяцы для расчета
            dt_obj = datetime.strptime(str(date_str), "%d.%m.%Y %H:%M:%S")
            if dt_obj.strftime("%Y-%m") != month:
                continue

            # Получаем сумму и чистим (убираем минус, меняем запятую и убираем ненужные пробелы)
            raw_amount = transaction.get("Сумма операции", 0)
            clean_amount = str(raw_amount).replace(',', '.').replace('-', '').strip()
            amount = float(clean_amount)
            # Исключаем сумму меньше 0
            if amount <= 0:
                continue
            # Если остаток от деления есть, округляем до следующего целого лимита
            if amount % limit == 0:
                rounded_amount = amount
            else:
                # (сумма // лимит + 1) * лимит дает следующее кратное число
                rounded_amount = (amount // limit + 1) * limit
            amount_investment = rounded_amount - amount
            amount_investment_bank += amount_investment
        except (ValueError, TypeError) as e:
            logger_investment_bank.error(f"Ошибка при обработке строки: {e}")
            continue
    return round(amount_investment_bank, 2)


def simple_search(search_data: str, transactions: list[dict]| None) -> str:
    """Функция, принимает на вход строку для поиска search_data и transactions — список словарей,
     содержащий информацию о транзакциях, возвращает JSON-ответ со всеми транзакциями, содержащими запрос
     в описании или категории."""

    logger_simple_search.info(f"Начало поиска по запросу {search_data}")

    # Если строка пустая возвращаем пустой список в формате JSON
    if not search_data:
        logger_simple_search.warning("Передан пустой поисковый запрос")
        return json.dumps([], ensure_ascii=False)

    # Если нет файла с данными возвращаем пустую строку
    if transactions is None:
        logger_simple_search.warning("Передан пустой файл для поиска данных")
        return json.dumps([], ensure_ascii=False)

    searched_transactions = []
    search_data_lower = search_data.lower()  # Приводим к нижнему регистру поисковую строку

    for transaction in transactions:
        try:
            # Получаем значения, заменяя None на пустую строку, чтобы не было исключения
            # и приводим к нижнему регистру .lower()
            description = str(transaction.get("Описание", "")).lower()
            category = str(transaction.get("Категория", "")).lower()

            # Проверяем вхождение строки в искомых полях в описании или категории
            if search_data_lower in description or search_data_lower in category:
                # Добавляем транзакцию если строка была найдена
                searched_transactions.append(transaction)

        except Exception as e:
            logger_simple_search.error(f"Ошибка при обработке транзакции {e}")
            continue

    logger_simple_search.info(f"Поиск завершен. Найдено совпадений: {len(searched_transactions)}")

    return json.dumps(searched_transactions, ensure_ascii=False, indent=4)


def search_with_phone_number(transactions: list[dict]) -> str:
    """Функция, принимает на вход transactions — список словарей, содержащий информацию о транзакциях,
    возвращает JSON-ответ со всеми транзакциями, содержащими в описании мобильные номера."""

    logger_search_with_phone_number.info(f"Начало поиска транзакций с телефонными номерами")

    searched_transactions = []
    # Компилируем паттерн для поиска транзакций с телефонными номерами
    phone_pattern = re.compile(r'\+?\d \d{3} \d{2,3}-?\d{2}-?\d{2}')

    for transaction in transactions:
        try:
            # Получаем значения, заменяя None на пустую строку, чтобы не было исключения
            # и приводим к нижнему регистру .lower()
            description = str(transaction.get("Описание", ""))

            # Проверяем найден ли нужный паттерн в описании транзакции
            if phone_pattern.search(description):
                # Добавляем транзакцию если паттерн был найден
                searched_transactions.append(transaction)

        except Exception as e:
            logger_search_with_phone_number.error(f"Ошибка при обработке транзакции {e}")
            continue

    logger_search_with_phone_number.info(f"Поиск завершен. Найдено совпадений: {len(searched_transactions)}")

    return json.dumps(searched_transactions, ensure_ascii=False, indent=4)



# if __name__ == "__main__":
#     data = read_excel(PATH_TO_FILE_EXCEL)
#     print(data)
#     print(cashback_benefit(data, "2021", "02"))
    # print(investment_bank("2021-03",data, 50))
    # print(simple_search('Переводы', data))
    # print(search_with_phone_number(data))