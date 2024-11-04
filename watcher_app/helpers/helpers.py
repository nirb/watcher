import decimal
import json
from .defs import *
from datetime import datetime


def currency_to_symbol_or_type(currency):
    if currency in CURRENCY_SYMBOLS:
        return CURRENCY_TYPES[CURRENCY_SYMBOLS.index(currency)]
    if currency in CURRENCY_TYPES:
        return CURRENCY_SYMBOLS[CURRENCY_TYPES.index(currency)]
    if currency in CURRENCY_TYPES:
        return currency

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
        return super().default(o)
