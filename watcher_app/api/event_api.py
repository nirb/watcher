from helpers.defs import *
from helpers.debug import print_debug
from ui.plots import Plot
from helpers.helpers import generate_id
from helpers.tables import get_row_index_by_col
import json


class EventApi:
    def __init__(self, db, table_name=EVENTS_TABLE_NAME):
        self.db = db
        self.events = []
        self.table_name = table_name

    def get_events(self):
        if len(self.events) == 0:
            self.events = self.db.get_table(self.table_name)
        return list(reversed(sorted(self.events, key=lambda item: item[COL_DATE])))

    def add_event(self, watcher, date, type, value, description):
        events = self.get_event_for_watcher(watcher)
        if any(item[COL_PARENT_ID] == watcher[COL_ID] and
               item[COL_VALUE] == value and
               item[COL_TYPE] == type and
               item[COL_DATE] == date for item in events):
            print_debug(
                "Event with the same date and value exist, ignorring !!!")
            return RET_FAILED
        row = {COL_ID: generate_id(),
               COL_PARENT_ID: watcher[COL_ID], COL_DATE: date, COL_TYPE: type,
               COL_VALUE: value, COL_DESCRIPTION: description}
        if self.db.add_row(self.table_name, row) != -1:
            self.events.append(row)
            print_debug("Add event succeded")
            return RET_OK
        else:
            print("Add event failed")
            return RET_FAILED

    def get_event_for_watcher(self, watcher):
        return list(
            filter(lambda item: item[COL_PARENT_ID] == watcher[COL_ID], self.get_events()))

    def show_events(self, watcher):
        watcher_events = self.get_event_for_watcher(watcher)
        if len(watcher_events) > 0:
            print_debug(f"show_events {watcher_events}")
            Plot().show_table(
                watcher_events, value_postfix=watcher[COL_CURRENCY] if COL_CURRENCY in watcher else "")
        else:
            print("No events found for this watcher")

    def update_event(self, parent_id, event_id, date, type, value, description):
        payload = {
            "Key": {
                "id": event_id
            },
            "UpdateExpression": "SET #parent_id = :parent_id , #date = :date, #type = :type, #value = :value, #description = :description",
            "ExpressionAttributeNames": {
                "#parent_id": "parent_id",
                "#date": "date",
                "#type": "type",
                "#value": "value",
                "#description": "description"
            },
            "ExpressionAttributeValues": {
                ":parent_id": parent_id,
                ":date": date,
                ":type": type,
                ":value": value,
                ":description": description
            }
        }
        print_debug(f"update_event {payload=}")
        if self.db.update_row(self.table_name, payload) == 0:
            row_index = get_row_index_by_col(
                COL_ID, event_id, self.get_events())
            if row_index != -1:
                self.events[row_index] = {
                    "id": event_id,
                    "parent_id": parent_id,
                    "date": date,
                    "type": type,
                    "value": value,
                    "description": description
                }
                return RET_OK
        return RET_FAILED

    def remove_event(self, event_id):
        if self.db.remove_row(self.table_name, key={"id": event_id}) == 0:
            print_debug(f"Event with id {event_id=} removed")
            self.events = []
            return RET_OK
        print(f"Fail to remove Event with id {event_id=}")
        return RET_FAILED

    def remove_all_events(self, watcher):
        events = self.get_event_for_watcher(watcher)
        if len(events) == 0:
            print(
                f"remove_all_events - No events found for watcher '{watcher[COL_NAME]}'")
        print(
            f"removing #{len(events)} events for watcher '{watcher[COL_NAME]}'")
        while True:
            events = self.get_event_for_watcher(watcher)
            if len(events) == 0:
                print_debug(
                    f"remove_all_events - all events removed for watcher '{watcher[COL_NAME]}'")
                break
            self.remove_event(events[0][COL_ID])
        return RET_OK
