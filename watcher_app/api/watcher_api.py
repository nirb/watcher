from helpers.defs import *
from helpers.debug import print_debug
from helpers.investment_calc import calculate_investment_info
from helpers.helpers import generate_id
from helpers.tables import get_row_by_name, get_row_index_by_col
from api.event_api import EventApi
from datetime import datetime


class WatcherApi:
    def __init__(self, db, event_api, table_name=WATCHERS_TABLE_NAME) -> None:
        self.watchers = []
        self.db = db
        self.event_api: EventApi = event_api
        self.table_name = table_name

    def get_watchers(self):
        if len(self.watchers) == 0:
            self.watchers = self.db.get_table(self.table_name)
        return list(sorted(self.watchers, key=lambda item: item[COL_NAME]))

    def get_watchers_names(self):
        return [r[COL_NAME] for r in self.get_watchers()]

    def get_watcher_events(self, watcher, event_type=None, fill_dates=False):
        watcher_events = list(
            filter(lambda item: item[COL_PARENT_ID] == watcher[COL_ID], self.event_api.get_events()))
        if event_type is not None:
            watcher_events = list(
                filter(lambda item: item[COL_TYPE] == event_type, watcher_events))
        if fill_dates:
            return self.fill_dates(watcher_events)

        return watcher_events

    def fill_dates(self, events):
        ret_list = []
        reversed_list = list(reversed(events))
        last_event = None
        for event in reversed_list:
            if len(ret_list) == 0:  # the first event
                ret_list.append(event)
                last_event = event.copy()
                continue
            last_date = datetime.strptime(last_event[COL_DATE], DATE_FORMAT)
            last_months = last_date.year*12+last_date.month
            current_date = datetime.strptime(event[COL_DATE], DATE_FORMAT)
            currrent_months = current_date.year*12+current_date.month
            while currrent_months > last_months+1:
                last_event = last_event.copy()
                last_event[COL_DESCRIPTION] = "copy last month!!!"
                last_months = last_date.year*12+last_date.month+1
                next_month = last_date.month+1 if last_date.month != 12 else 1
                next_year = last_date.year if last_date.month != 12 else last_date.year+1
                last_event[COL_DATE] = datetime(
                    next_year, next_month, 6).strftime(DATE_FORMAT)
                last_date = datetime.strptime(
                    last_event[COL_DATE], DATE_FORMAT)
                ret_list.append(last_event)
            last_event = event.copy()
            ret_list.append(event)
        return list(reversed(ret_list))

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
        watcher_events = self.get_watcher_events(watcher)
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
