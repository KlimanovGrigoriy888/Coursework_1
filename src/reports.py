import os
import pandas as pd
from typing import Optional

PATH_TO_FILE_EXCEL = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "operations.xlsx")

def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """Функция принимает на вход: датафрейм с транзакциями, название категории, опциональную дату.
    Если дата не передана, то берется текущая дата. Функция возвращает траты по заданной категории
    за последние три месяца (от переданной даты)"""

    # 1. Работаем с копией и убираем пустые номера карт через .notnull()
    df = transactions.copy()
    df = df[df["Категория"].notnull()]
