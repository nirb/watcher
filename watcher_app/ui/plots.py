from tabulate import tabulate
from helpers.defs import *
from helpers.debug import get_debug_mode, print_debug
from helpers.helpers import currency_to_symbol_or_type, int_to_str, capitalize_list, DecimalEncoder
import matplotlib.pyplot as plt
import pandas as pd
from mplcursors import cursor
from matplotlib.ticker import FuncFormatter
import json


class Plot:
    def sort_headers(self, headers):
        tmp = headers.copy()
        ret = []
        orders = [COL_NAME, COL_INVESTED, ROI, COL_VALUE, COL_PROFIT_ITD, COL_COMMITMENT,
                  COL_UNFUNDED, COL_CURRENCY, COL_TYPE]
        for o in orders:
            if o in headers:
                ret.append(o)
                tmp.remove(o)
        for t in tmp:
            ret.append(t)
        # print_debug(f"sort_headers {ret=}")
        return ret

    def clean_headers(self, headers):
        if not get_debug_mode():
            remove_list = [COL_ID, COL_PARENT_ID, COL_COMMITMENT,
                           COL_CURRENCY, COL_ACTIVE]

            for remove in remove_list:
                if remove in headers:
                    headers.remove(remove)
        return headers

    def build_headers(self, rows, sort_headers=True):
        all_keys = set()
        for r in rows:
            all_keys.update(r.keys())
        headers = list(all_keys)
        headers = self.clean_headers(headers)
        if sort_headers:
            headers = self.sort_headers(headers)
        print_debug(json.dumps(headers, indent=2, cls=DecimalEncoder))
        return headers

    def show_table(self, rows, value_postfix="", sort_headers=True, headers=None):
        print_debug(
            f"show_table {json.dumps(rows,indent=2,cls=DecimalEncoder)}")
        if len(rows) > 0:
            if headers is None:
                headers = self.build_headers(rows)
            data = []
            for r in rows:
                row = ["" for i in headers]
                # print_debug(f"{row=}")
                for index, h in enumerate(headers):
                    if h in r:
                        if h in INT_COLS_TYPE:
                            if COL_CURRENCY in r:
                                value = int(r[h])
                                entry = f"{currency_to_symbol_or_type(r[COL_CURRENCY])} {int_to_str(value)}"
                            else:
                                entry = f"{value_postfix} {int(r[h]):,}"
                        else:
                            entry = r[h]
                        row[index] = entry
                data.append(row)
            print(tabulate(data, headers=capitalize_list(
                headers), tablefmt="rounded_grid"))
        else:
            print("Table is empty")

    def value_formater(self, value, tick_number):
        return f'{value:,.0f}'  # Format large numbers with commas

    def show_plot(self, data, title, currency):
        df = pd.DataFrame(data)
        # df["date"] = df["date"].sort()
        fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
        ax.bar(df["date"], df["value"])

        ax.set(ylabel=currency, title=title)
        ax.grid()
        plt.yticks()

        xticks = []
        number_of_dates = len(df["date"])
        if number_of_dates > 3:
            xticks.append(df["date"][0])
            xticks.append(df["date"][int(number_of_dates/2)])
            xticks.append(df["date"][number_of_dates-1])

        plt.xticks(ticks=xticks)
        plt.gca().yaxis.set_major_formatter(FuncFormatter(self.value_formater))
        cursor(hover=True)
        plt.show()
