import json
import os
from datetime import datetime
from typing import Any

from src.logger import setup_logging
from src.utils import read_excel

PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")
data = read_excel(PATH_TO_FILE_EXCEL)

logger_cashback_benefit = setup_logging("read_json")
logger_investment_bank = setup_logging("read_json")

def cashback_benefit(data_list: list[dict[str, Any]], year: int, month: int) -> str:
    """
    Анализирует список транзакций и подсчитывает потенциальный кешбэк
    по категориям за указанный год и месяц.
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

    # Округляем итоговые суммы до целого числа (как в вашем ТЗ)
    result = {cat: int(total) for cat, total in category_cashback.items()}

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
            # 1. Извлекаем данные даты из списка транзакций
            date_str = transaction.get("Дата операции")
            if not date_str:
                continue
            # Преобразуем полученные данные даты в объект datatime и пропускаем ненужные месяцы для расчета
            dt_obj = datetime.strptime(str(date_str), "%d.%m.%Y %H:%M:%S")
            if dt_obj.strftime("%Y-%m") != month:
                continue

            # Получаем сумму и чистим (убираем минус и меняем запятую)
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


if __name__ == "__main__":
    print(data)
    print(cashback_benefit(data, "2021", "02"))
    # print(investment_bank("2021-03",data, 50))