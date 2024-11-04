from random import randint
from helpers.defs import *

COMITTED = 3333
NUMBER_OF_WATCHERS = 5
NUMBER_OF_EVENTS = 8


def rand_from_list(list_of_items):
    return list_of_items[randint(0, len(list_of_items)-1)]


def number_of_watchers(appApi):
    return len(appApi.get_watcher_names())


def generate_watcher(appApi):
    return {
        COL_NAME: f"test_watcher-{number_of_watchers(appApi)}",
        COL_CURRENCY: rand_from_list(CURRENCY_TYPES),
        COL_TYPE: INVESTMENT_WATCHER_TYPES[0],
        COL_COMMITMENT: COMITTED,
        COL_UNFUNDED: 2,
        COL_ACTIVE: rand_from_list([YES, NO])}


def test_printer(msg, count_lines=1):
    nums = 10
    for x in range(count_lines):
        print(f'{nums*"!"} {msg} {nums*"!"}')


def test_function_printer(func):
    def wrapper(*args, **kwargs):
        # print(f"----> Starting '{func.__name__}' ----")
        ret = func(*args, **kwargs)
        print(f"<---- '{func.__name__}' Ended  ----", end="\n\n")
        return ret
    return wrapper
