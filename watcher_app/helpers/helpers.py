import decimal
import json
from .defs import *
from datetime import datetime


def currency_to_symbol_or_type(currency):
    # print("currency_to_symbol_or_type1", currency)
    # print("currency_to_symbol_or_type2", CURRENCY_SYMBOLS)
    # print("currency_to_symbol_or_type3", CURRENCY_TYPES)
    if currency in CURRENCY_SYMBOLS:
        return CURRENCY_TYPES[CURRENCY_SYMBOLS.index(currency)]
    if currency in CURRENCY_TYPES:
        return CURRENCY_SYMBOLS[CURRENCY_TYPES.index(currency)]

    return None


def int_to_str(value):
    if value >= 0:
        return f"{int(value):,}"
    return f"({int(-1*value):,})"


def generate_id():
    return datetime.now().strftime('%Y:%m:%d:%H:%M:%S:%f')


def capitalize_list(list_of_strings):
    return [e if e[:1].istitle() else e.capitalize() for e in list_of_strings]


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, type(int)):
            return int_to_str(o)
        return super().default(o)


def get_months_list(year=None):
    if year is None:  # return just the month
        return [datetime(2023, i, 1).strftime("%b") for i in range(1, 13)]
    return [datetime(year, i, 1).strftime(DATE_FORMAT) for i in range(1, 13)]


def date_to_month_str(date):
    return date.strftime("%b")
