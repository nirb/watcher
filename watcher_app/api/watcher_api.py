from helpers.defs import *
from helpers.debug import print_debug
from helpers.investment_calc import calculate_investment_info
from helpers.helpers import generate_id
from helpers.tables import get_row_by_name, get_row_index_by_col


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
