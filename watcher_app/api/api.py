from db.local_db import LocalDb


from db.remote_db import RemoteDb
from helpers.defs import *
from .watcher_api import WatcherApi
from .event_api import EventApi


class AppApi:
    def __init__(self, local_db=False, test_mode=False) -> None:
        table_names = TEST_TABLE_NAMES if test_mode else PROD_TABLE_NAMES
        self.db = LocalDb(table_names) if local_db else RemoteDb()
        table_name = EVENTS_TABLE_NAME_TEST if test_mode else EVENTS_TABLE_NAME
        self.event_api = EventApi(self.db, table_name)
        table_name = WATCHERS_TABLE_NAME_TEST if test_mode else WATCHERS_TABLE_NAME
        self.watcher_api = WatcherApi(
            self.db, self.event_api, table_name=table_name)
        self.advisors_table_name = ADVISORS_TABLE_NAME_TEST if test_mode else ADVISORS_TABLE_NAME

    def get_watchers(self):
        return self.watcher_api.get_watchers()

    def add_watcher(self, watcher):
        return self.watcher_api.add_watcher(watcher)

    def get_watcher_names(self):
        return self.watcher_api.get_watchers_names()

    def get_watcher_by_name(self, name):
        return self.watcher_api.get_watcher_by_name(name)

    def get_watcher_info(self, watcher):
        return self.watcher_api.get_watcher_info(watcher)

    def update_watcher(self, watcher):
        return self.watcher_api.update_watcher(watcher)

    def remove_watcher_by_name(self, name):
        return self.watcher_api.remove_watcher_by_name(name)

    # events
    def show_events(self, watcher):
        return self.event_api.show_events(watcher)

    def add_event(self, watcher, date, type, value, description):
        return self.event_api.add_event(watcher, date, type, value, description)

    def update_event(self, parent_id, event_id, date, type, value, description):
        return self.event_api.update_event(parent_id, event_id, date, type,
                                           value, description)

    def remove_event(self, event_id):
        return self.event_api.remove_event(event_id)

    def remove_all_events(self, watcher):
        return self.event_api.remove_all_events(watcher)

    # advisors
    def get_advisors(self):
        return self.db.get_table(self.advisors_table_name)

    def add_advisor(self, advisor_name, phone, mail):
        return self.db.add_row(self.advisors_table_name,
                               row={COL_ID: advisor_name, COL_PHONE: phone, COL_MAIL: mail})

    def remove_advisor(self, advisor_name):
        return self.db.remove_row(self.advisors_table_name, key={COL_ID: advisor_name})
