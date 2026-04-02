import json
import os
from datetime import timedelta
from idlelib.iomenu import encoding

import pandas as pd
from typing import Optional, Callable, Any
import datetime

from mypy.strconv import indent

from src.logger import setup_logging
from src.utils import read_excel_to_df
from functools import wraps

PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")
logger_data_for_reports = setup_logging("get_range_data_for_reports")
logger_spending_by_category = setup_logging("spending_by_category")
logger_spending_by_weekday = setup_logging("spending_by_weekday")


def log_record(filename: str = "record_file.json") -> Callable:
    """Декоратор для функции, записывает в файл результат, который возвращает функция, записывает его в файл
     record_file.txt:
    Если принимаемая функция выполнилась без исключений в лог записывается результат работы функции
    Если при исполнении функции возникло исключение в лог записывается сообщение о выпавшем исключении
    декорируемой функции."""

    def wrapper(func: Callable) -> Callable:
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            try:
                result = func(*args, **kwargs)
                # Если результат — DataFrame, сохраняем его сразу в json файл
                if isinstance(result, (pd.DataFrame, pd.Series)):
                    # Если это Series, конвертируем в DataFrame для корректного JSON
                    output_df = result.to_frame() if isinstance(result, pd.Series) else result
                    # Записываем результат функции в файл, orient='records' сделает список словарей,
                    # force_ascii=False сохранит кириллицу
                    output_df.to_json(filename, orient='records', indent=4, force_ascii=False)
                    print(f"Успех: результат функции {func.__name__} записан в {filename}")
                # Если это не DataFrame и Series выводим сообщение, что функция вернула другой тип данных
                else:
                    print(f"Предупреждение: функция {func.__name__} вернула {type(result)}, запись пропущена.")
                return result
            except Exception as e:
                error_info = {"function_name": func.__name__, "error": str(e)}
                with open(filename, "w", encoding="utf-8") as file:
                    json.dump(error_info, file, ensure_ascii=False, indent=4)
                # Выводим ошибку дальше
                raise e
        return inner
    return wrapper


def get_range_data_for_reports(target_str_date: str = None) -> datetime:
    """Принимает указанную дату в формате строки "dd.mm.YYYY HH:MM:SS" возвращает диапазон:
     от трех месяцев назад до указанной даты в формате datetime в виде start_date, end_date."""

    logger_data_for_reports.info(f"Начало создания диапазона дат в три месяца")
    # Если дата пустая или не строка — возвращаем текущую дату и время в формате строки
    if isinstance(target_str_date, str):
        logger_data_for_reports.info(f"Дата в формате 'str' = {target_str_date} , преобразуем в формат datetime ")
        try:
            end_date_obj = datetime.datetime.strptime(target_str_date, '%d.%m.%Y %H:%M:%S')
        except ValueError:  # Если исключение по введенной дате возвращаем текущую дату
            logger_data_for_reports.error(f"Не правильно введена заданная дата, по этому берем текущую "
                                          f"дату создания диапазона дат в три месяца")
            end_date_obj = datetime.datetime.now()

    # Если это уже объект datetime — используем его как есть
    elif isinstance(target_str_date, datetime.datetime):
        logger_data_for_reports.info(f"Дата уже в формате datetime")
        end_date_obj = target_str_date

    # Во всех остальных случаях (None, числа, другой тип) — берем "сейчас"
    else:
        logger_data_for_reports.info(f"Дата введена в виде = None, числа, другой тип, по этому берем дату 'сейчас'")
        end_date_obj = datetime.datetime.now()

    # Вычисляем дату "3 месяца назад"
    start_date_obj = end_date_obj - timedelta(days=90)

    logger_data_for_reports.info(f"Возвращаем результат функции")
    return start_date_obj, end_date_obj


@log_record()
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """Функция принимает на вход: датафрейм с транзакциями, название категории, опциональную дату в формате
    DD.MM.YYYY HH:MM:SS. Если дата не передана, то берется текущая дата. Функция возвращает траты по заданной
    категории за последние три месяца (от переданной даты)"""

    logger_spending_by_category.info(f"Начало работы функции")
    # Работаем с копией и чистим категорию: убираем строки со значениями равными NaN, убираем пробелы в столбце Категория .notnull()
    logger_spending_by_category.info(f"обработка строк категории от ненужных пробелов и значений NaN")
    df = transactions.copy()
    df = df[df["Категория"].notnull()]
    df["Категория"] = df["Категория"].str.strip()

    # Подготавливаем столбец Сумма платежа: заменяем запятую на точку и переводим в float
    logger_spending_by_category.info(f"В строках Сумма платежа меняем запятые на точки")
    df["Сумма платежа"] = (df["Сумма платежа"].astype(str).str.replace(",", ".").astype(float))

    # Подготовка новой колонки с датой для правильной сортировки
    # df["Дата для фильтра"] = df["Дата операции"].map(lambda x: datetime.datetime.strptime(x, '%m.%d.%Y %H:%M:%S'))
    logger_spending_by_category.info(f"Подготовка новой колонки Дата для фильтра для правильной сортировки")
    df["Дата для фильтра"] = pd.to_datetime(df["Дата операции"], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    # Удаляем строки со значением NaN, где дата не определилась
    df = df.dropna(subset=["Дата для фильтра"])

    # Получаем диапазон дат поиска транзакций через внешнюю функцию
    logger_spending_by_category.info(f"Получаем диапазон дат поиска транзакций через внешнюю функцию")
    start_date, end_date = get_range_data_for_reports(date)

    # Фильтрация по заданным датам и категории
    logger_spending_by_category.info(
        f"Фильтруем датафрейм по заданным датам и категории и 'Сумма платежа' со значением меньше ноля")
    filtered_df_by_category = df.loc[(df["Дата для фильтра"] >= start_date) & (df["Дата для фильтра"] <= end_date) & (
            df["Категория"] == category) & (df['Сумма платежа'] <= 0)]

    # Получаем траты по искомой категории
    logger_spending_by_category.info(f"Получаем траты по искомой категории: {category}")
    # spending_categories = abs(filtered_df_by_category['Сумма платежа'].sum())
    spending_categories = filtered_df_by_category.groupby("Категория").agg({'Сумма платежа': sum}).reset_index()
    spending_categories = spending_categories['Сумма платежа'].abs()

    return spending_categories


@log_record()
def spending_by_weekday(transactions: pd.DataFrame,
                        date: Optional[str] = None) -> pd.DataFrame:
    """ Функция принимает на вход: датафрейм с транзакциями, опциональную дату. Если дата не передана,
     то берется текущая дата. Функция возвращает средние траты в каждый из дней недели за последние
     три месяца (от переданной даты)."""
    logger_spending_by_weekday.info("Начало работы функции")
    # Работаем с копией и убираем строки со значениями равными NaN, убираем пробелы в столбце Категория .notnull()
    logger_spending_by_weekday.info(
        "Работаем с копией и убираем строки со значениями равными NaN с .notnull(), убираем пробелы в столбце Категория")
    df = transactions.copy()
    df = df[df["Категория"].notnull()]
    df["Категория"] = df["Категория"].str.strip()

    # Заменяем запятую на точку и переводим в float с помощью функции astype("требуемый тип данных")
    logger_spending_by_weekday.info(
        "В 'Сумма платежа' Заменяем запятую на точку и переводим в float с помощью функции astype('требуемый тип данных')")
    df["Сумма платежа"] = (df["Сумма платежа"].astype(str).str.replace(",", ".").astype(float))

    # Подготовка новой колонки с датой для правильной сортировки с помощью функции pd.to_datetime
    # df["Дата для фильтра"] = df["Дата операции"].map(lambda x: datetime.datetime.strptime(x, '%m.%d.%Y %H:%M:%S'))
    logger_spending_by_weekday.info(
        "Подготовка новой колонки datetime для правильной сортировки")
    df["Дата для фильтра"] = pd.to_datetime(df["Дата операции"], format='%d.%m.%Y %H:%M:%S', errors='coerce')
    # Удаляем строки, где дата не определилась с помощью функции df.dropna()
    df = df.dropna(subset=["Дата для фильтра"])

    # Получаем диапазон дат поиска транзакций через внешнюю функцию
    logger_spending_by_weekday.info(
        "Получаем диапазон дат поиска транзакций через внешнюю функцию")
    start_date, end_date = get_range_data_for_reports(date)

    # Фильтрация по заданным датам
    logger_spending_by_weekday.info(
        "Фильтруем датафрейм по заданным датам и 'Сумма платежа' со значением меньше ноля")
    filtered_df_range_date = df.loc[(df["Дата для фильтра"] >= start_date) & (df["Дата для фильтра"] <= end_date)
                                    & (df['Сумма платежа'] <= 0)]

    # Берем модуль суммы для удобства отображения среднего используя функцию abs()
    logger_spending_by_weekday.info(
        "'Сумма платежа' приводим к модулю для правильного вывода")
    filtered_df_range_date["Сумма платежа"] = filtered_df_range_date["Сумма платежа"].abs()

    # Подготовка новой колонки с днями недели с помощью функции получения дня недели и объекта datetime - dt.day_name()
    logger_spending_by_weekday.info(
        "Подготовка новой колонки 'week_dey' с днями недели с помощью функции получения дня недели"
        " и объекта datetime - dt.day_name()")
    filtered_df_range_date["week_dey"] = filtered_df_range_date["Дата для фильтра"].dt.day_name()

    # Группировка по дням недели и категориям и расчет среднего значения для суммы платежа, с округлением до 2 знака,
    # далее сброс индекса
    logger_spending_by_weekday.info("Группировка и расчет средних трат в каждый из дней недели")
    result = (filtered_df_range_date.groupby(["week_dey", "Категория"])["Сумма платежа"]
              .mean().round(2)  # Округляем до 2 знака
              .reset_index()  # «подписи» "week_dey", "Категория" из индекса преобразуем обратно в столбцы датафрейма
              .rename(columns={"Сумма платежа": "Средние траты"})).sort_values(by="week_dey")

    logger_spending_by_weekday.info(f"Получаем средние траты по дням недели")
    return result


# if __name__ == "__main__":
    # print(get_range_data_for_reports("28.05.2025 15:29:44")) # "28.05.2025 15:29:44"
    # df_data = read_excel_to_df(PATH_TO_FILE_EXCEL)
    # print(df_data.head(5))
    # print(df_data.to_json(orient='records', force_ascii=False))
    # print(spending_by_category(df_data, "Топливо", "29.12.2021 22:28:47")) # "29.12.2021 22:28:47"
    # print(type(spending_by_category(df_data, "Топливо", "29.12.2021 22:28:47")))
    # print(spending_by_weekday(df_data, "29.12.2021 22:28:47"))

# # Вычисляем "3 месяца назад"
#    # Вычитаем из текущего месяца 3. Если уходим в минус — уменьшаем год.
#    month = current_date_obj.month - 3
#    year = current_date_obj.year
#    if month <= 0:
#        month += 12
#        year -= 1
#
#    try:
#        # Пытаемся создать ту же дату, но 3 месяца назад
#        start_date_obj = current_date_obj.replace(year=year, month=month)
#    except ValueError:
#        logger_data_for_reports.error(f"Заданная дата имеет день месяца которого нет в прошлом, по этому "
#                                     f"берем 1-е число полученного прошлого месяца и вычитаем 1 день")
#        # Если дата прошлого месяца имеется, например текущая 31 марта, а в декабре только 31.
#        # но если текущая 31 мая, а три месяца назад 28(29) февраля, то replace выдаст ошибку.
#        # В таком случае просто берем 1-е число полученного прошлого месяца и вычитаем 1 день.
#        start_date_obj = current_date_obj.replace(year=year, month=month, day=1) - datetime.timedelta(days=1)
#            # Форматируем результат
#            logger_data_for_reports.info(f"вывод результата функции")
#            start_date = start_date_obj.strftime('%Y.%m.%d %H:%M:%S')
#            end_date = current_date_obj.strftime('%Y.%m.%d %H:%M:%S')
