from helpers.investment_calc import calculate_investment_profit
from helpers.defs import *
from api.api import AppApi

appApi = AppApi(local_db=False)


def get_watchers_summary_currency(watchers):
    rows = []
    for currency in CURRENCY_TYPES:
        currency_sum = 0
        invested = 0
        ytd = 0
        commited = 0
        for w in watchers:
            if w[COL_CURRENCY] == currency:
                watcher_info = appApi.get_watcher_info(w)
                if watcher_info is not None:
                    currency_sum += watcher_info[COL_FINANCE][COL_VALUE]
                    invested += watcher_info[COL_FINANCE][COL_INVESTED]
                    print(
                        f"watcher {w[COL_NAME]} ITD {watcher_info[COL_FINANCE][COL_PROFIT_YTD]}")
                    ytd += watcher_info[COL_FINANCE][COL_PROFIT_YTD]
                    commited += watcher_info[COL_FINANCE][COL_COMMITMENT]
                else:
                    print("Error watcher_info not created")

        row = {COL_CURRENCY: currency,
               COL_VALUE: currency_sum,
               COL_INVESTED: invested,
               COL_PROFIT_ITD: calculate_investment_profit(invested, currency_sum),
               COL_PROFIT_YTD: ytd,
               COL_COMMITMENT: commited,
               COL_UNFUNDED: invested-commited}

        rows.append(row)
    return rows


def get_watchers_summary_date(watchers):
    pass
