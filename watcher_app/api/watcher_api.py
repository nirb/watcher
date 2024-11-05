from helpers.defs import *
from helpers.debug import print_debug
from helpers.investment_calc import calculate_investment_info, calculate_investment_profit
from helpers.helpers import int_to_str, generate_id, capitalize_list, DecimalEncoder
from tabulate import tabulate
from ui.plots import Plot
from helpers.tables import get_row_by_name, get_row_index_by_col
import json


class WatcherApi:
    def __init__(self, db, event_api, table_name=WATCHERS_TABLE_NAME) -> None:
        self.watchers = []
        self.db = db
        self.event_api = event_api
        self.table_name = table_name

    def get_watchers(self):
        if len(self.watchers) == 0:
            self.watchers = self.db.get_table(self.table_name)
        return list(sorted(self.watchers, key=lambda item: item[COL_NAME]))

    def get_watchers_names(self):
        return [r[COL_NAME] for r in self.get_watchers()]

    def add_watcher(self, watcher):
        # validate watcher
        if len(watcher[COL_NAME]) < 3:
            print("row name is too short")
            return RET_FAILED

        # check for name duplication
        if len(list(filter(lambda item: item[COL_NAME] == watcher[COL_NAME], self.get_watchers()))) != 0:
            print(f"Row with name '{watcher[COL_NAME]}' already exists.")
            return RET_FAILED

        watcher[COL_ID] = generate_id()
        if self.db.add_row(self.table_name, watcher) != -1:
            self.watchers.append(watcher)
            print(f"Add watcher '{watcher[COL_NAME]}' succeded")
            return RET_OK
        return RET_FAILED

    def get_watcher_info(self, watcher):
        watcher_events = list(filter(lambda item: item[COL_PARENT_ID] == watcher[COL_ID],
                                     self.event_api.get_events()))

        return {COL_EVENTS: watcher_events,
                COL_FINANCE: calculate_investment_info(watcher_events)}

    def show_watcher_summary(self):
        watchers = self.get_watchers()
        if len(watchers) > 0:
            print("Watchers summary")
            rows = []
            for currency in CURRENCY_TYPES:
                currency_sum = 0
                invested = 0
                ytd = 0
                commited = 0
                for w in watchers:
                    if w[COL_CURRENCY] == currency:
                        watcher_info = self.get_watcher_info(w)
                        print_debug(
                            f"get_watcher_info {json.dumps(watcher_info,indent=4,cls=DecimalEncoder)}")
                        if watcher_info is not None:
                            currency_sum += watcher_info[COL_FINANCE][COL_VALUE]
                            invested += watcher_info[COL_FINANCE][COL_INVESTED]
                            ytd += watcher_info[COL_FINANCE][COL_PROFIT_YTD]
                            commited += watcher_info[COL_FINANCE][COL_COMMITMENT]

                row = {COL_CURRENCY: currency,
                       COL_VALUE: currency_sum,
                       COL_INVESTED: invested,
                       COL_PROFIT_ITD: calculate_investment_profit(invested, currency_sum),
                       COL_PROFIT_YTD: ytd,
                       COL_COMMITMENT: commited,
                       COL_UNFUNDED: invested-commited}

                rows.append(row)
            print_debug(json.dumps(rows, indent=2, cls=DecimalEncoder))
            Plot().show_table(rows, sort_headers=False)

    def show_watchers(self):
        watchers = self.get_watchers()
        if len(watchers) == 0:
            print("No Watchers found, create the first one")
            return

        print_debug(json.dumps(self.get_watchers(),
                    indent=4, cls=DecimalEncoder))

        self.show_watcher_summary()
        for w in watchers:
            watcher_info = self.get_watcher_info(w)
            if watcher_info:
                w[COL_VALUE] = watcher_info[COL_FINANCE][COL_VALUE]
                w[COL_PROFIT_ITD] = watcher_info[COL_FINANCE][COL_PROFIT_ITD]
                w[COL_PROFIT_YTD] = watcher_info[COL_FINANCE][COL_PROFIT_YTD]
                w[COL_INVESTED] = watcher_info[COL_FINANCE][COL_INVESTED]
                w[COL_DIST_YTD] = watcher_info[COL_FINANCE][COL_DIST_YTD]
                w[COL_DIST_ITD] = watcher_info[COL_FINANCE][COL_DIST_ITD]
                w[ROI] = watcher_info[COL_FINANCE][ROI]
                w[COL_EVENTS_COUNT] = len(watcher_info[COL_EVENTS_COUNT])
                w[XIRR] = watcher_info[COL_FINANCE][XIRR]
                w[COL_COMMITMENT] = watcher_info[COL_FINANCE][COL_COMMITMENT]
                w[COL_UNFUNDED] = watcher_info[COL_FINANCE][COL_UNFUNDED]
                w[MONTHS] = watcher_info[COL_FINANCE][MONTHS]
        Plot().show_table(self.get_watchers(),
                          headers=[COL_NAME, COL_VALUE, COL_INVESTED, COL_DIST_ITD, ROI, MONTHS])
        Plot().show_table(self.get_watchers(),
                          headers=[COL_NAME, COL_PROFIT_ITD, COL_PROFIT_YTD, COL_DIST_YTD, COL_UNFUNDED, XIRR])

    def remove_watcher_by_name(self, name):
        print_debug(f"remove_watcher_by_name {name=}")
        watcher = self.get_watcher_by_name(name)
        if watcher == -1:
            print(f"Can't find watcher with name '{name}'")
            return RET_FAILED
        # check that watcher ha no events
        event_index = get_row_index_by_col(
            COL_PARENT_ID, watcher[COL_ID], self.event_api.get_events())

        if event_index != -1:
            print_debug(
                f"This Watcher '{name}' hase assosiate events, please remove the events first")
            return RET_FAILED

        print_debug(f"{watcher=}")
        if self.db.remove_row(
                table_name=self.table_name,
                key={"id": watcher[COL_ID]}) != -1:
            print_debug(self.watchers)
            row_index = get_row_index_by_col(
                COL_NAME, name, self.get_watchers())
            print_debug(
                f"pop from watchers {row_index} {self.get_watchers_names()}")
            self.watchers = []
            print_debug(f"after pop from watchers {self.get_watchers_names()}")
            print_debug(f"Removing watcher '{name}' succedded.")
            return RET_OK
        else:
            print(f"Removing watcher '{name}' Failed.")
            return RET_FAILED

    def get_watcher_by_name(self, name):
        return get_row_by_name(name, self.get_watchers())

    def update_watcher(self, watcher):
        payload = {
            "Key": {
                "id": watcher[COL_ID]
            },
            "UpdateExpression": f"SET \
                #{COL_NAME} = :{COL_NAME} ,\
              #{COL_CURRENCY} = :{COL_CURRENCY},\
              #{COL_TYPE} = :{COL_TYPE},\
              #{COL_ACTIVE} = :{COL_ACTIVE},\
              #{COL_COMMITMENT} = :{COL_COMMITMENT},\
              #{COL_UNFUNDED} = :{COL_UNFUNDED}",
            "ExpressionAttributeNames": {
                f"#{COL_NAME}": f"{COL_NAME}",
                f"#{COL_CURRENCY}": f"{COL_CURRENCY}",
                f"#{COL_TYPE}": f"{COL_TYPE}",
                f"#{COL_ACTIVE}": f"{COL_ACTIVE}",
                f"#{COL_COMMITMENT}": f"{COL_COMMITMENT}",
                f"#{COL_UNFUNDED}": f"{COL_UNFUNDED}"
            },
            "ExpressionAttributeValues": {
                f":{COL_NAME}": watcher[COL_NAME],
                f":{COL_CURRENCY}": watcher[COL_CURRENCY],
                f":{COL_TYPE}": watcher[COL_TYPE],
                f":{COL_ACTIVE}": watcher[COL_ACTIVE],
                f":{COL_COMMITMENT}": watcher[COL_COMMITMENT],
                f":{COL_UNFUNDED}": watcher[COL_UNFUNDED],
            }
        }
        return self.db.update_row(self.table_name, payload)
