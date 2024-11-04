import unittest
from api.api import AppApi
from helpers.defs import *
from test.helper import number_of_watchers, test_function_printer, \
    generate_watcher, NUMBER_OF_WATCHERS, NUMBER_OF_EVENTS, \
    rand_from_list
from datetime import datetime
import json

appApi = AppApi(local_db=True, test_mode=True)


class TestEvents(unittest.TestCase):
    @test_function_printer
    def test_2_1_start(self):
        self.test_cleanup(show=False)
        self.assertEqual(number_of_watchers(appApi), RET_OK)

    @test_function_printer
    def test_2_2_add_watchers(self):
        for x in range(NUMBER_OF_WATCHERS):
            self.assertEqual(appApi.add_watcher(
                generate_watcher(appApi)), RET_OK)

    @test_function_printer
    def test_2_3_add_events(self):
        for index, name in enumerate(appApi.get_watcher_names()):
            watcher = appApi.get_watcher_by_name(name)
            self.assertNotEqual(watcher, RET_FAILED)
            date = datetime.now().strftime(DATE_FORMAT)
            print(f"adding {NUMBER_OF_EVENTS+index} to '{name}'")
            for event_index in range(NUMBER_OF_EVENTS+index):
                self.assertEqual(appApi.add_event(
                    watcher, date, INVESTMENT_EVENT_TYPES[0],
                    200*event_index, f'test event {event_index}'), RET_OK)

    @test_function_printer
    def test_2_4_add_duplicate_event(self):
        for watcher_name in appApi.get_watcher_names():
            watcher = appApi.get_watcher_by_name(watcher_name)
            info = appApi.get_watcher_info(watcher)
            # appApi.show_watchers()
            # print("!!!!", info, watcher_name)
            selected_event = info["events"][0]
            self.assertEqual(appApi.add_event(watcher,
                             selected_event[COL_DATE],
                             selected_event[COL_TYPE],
                             selected_event[COL_VALUE],
                             "doesnt metter"), RET_FAILED)
            remove_marker = f"remove-me-{watcher_name}"
            # add event with the same date, diff value
            self.assertEqual(appApi.add_event(watcher,
                                              selected_event[COL_DATE],
                                              selected_event[COL_TYPE],
                                              selected_event[COL_VALUE]+100,
                                              remove_marker), RET_OK)
            # remove the added event
            info = appApi.get_watcher_info(watcher)
            for e in info["events"]:
                if e[COL_DESCRIPTION] == remove_marker:
                    self.assertEqual(appApi.remove_event(e[COL_ID]), RET_OK)

    @test_function_printer
    def test_2_5_count_events(self):
        for index, name in enumerate(appApi.get_watcher_names()):
            watcher = appApi.get_watcher_by_name(name)
            info = appApi.get_watcher_info(watcher)
            self.assertEqual(len(info["events"]), NUMBER_OF_EVENTS+index)
            print(
                f"wathcer {watcher[COL_NAME]} has {len(info['events'])} events.")

    @test_function_printer
    def test_2_6_try_to_remove_watcher_with_events(self):
        watcher_names = appApi.get_watcher_names()
        for i in range(10):
            watcher_name = rand_from_list(watcher_names)
            self.assertEqual(appApi.remove_watcher_by_name(
                watcher_name), RET_FAILED)

    @test_function_printer
    def test_2_7_update_events(self):
        for index, name in enumerate(appApi.get_watcher_names()):
            watcher = appApi.get_watcher_by_name(name)
            watcher_info = appApi.get_watcher_info(watcher)
            values_befor_and_after = []
            for event_index, e in enumerate(watcher_info["events"]):
                new_value = e[COL_VALUE]+event_index
                values_befor_and_after.append(
                    (e[COL_ID], new_value))
                appApi.update_event(
                    watcher[COL_ID], e[COL_ID], e[COL_DATE], e[COL_TYPE], new_value, e[COL_DESCRIPTION]+"-updated")
            watcher_info = appApi.get_watcher_info(watcher)
            # check updated value
            for event_index, e in enumerate(watcher_info["events"]):
                for v in values_befor_and_after:
                    if v[0] == e[COL_ID]:
                        # print(f"testing update {e[COL_ID]} , {e[COL_VALUE]}")
                        self.assertEqual(e[COL_VALUE], v[1])

    @test_function_printer
    def test_2_8_remove_event(self):
        for name in appApi.get_watcher_names():
            watcher = appApi.get_watcher_by_name(name)
            watcher_info = appApi.get_watcher_info(watcher)
            number_of_events_befor_remove = len(watcher_info["events"])
            number_of_events_to_remove = 3
            for i in range(number_of_events_to_remove):
                watcher_info = appApi.get_watcher_info(watcher)
                event_ids = list(
                    map(lambda event: event[COL_ID], watcher_info["events"]))
                self.assertEqual(appApi.remove_event(
                    rand_from_list(event_ids)), RET_OK)
            watcher_info = appApi.get_watcher_info(watcher)
            number_of_events_afer_remove = len(watcher_info["events"])
            self.assertEqual(number_of_events_afer_remove,
                             number_of_events_befor_remove-number_of_events_to_remove)

    @ test_function_printer
    def test_cleanup(self, show=True):
        if show:
            appApi.show_watchers()
        # remove all events and wathcers
        for watcher_name in appApi.get_watcher_names():
            watcher = appApi.get_watcher_by_name(watcher_name)
            print("!!!!! removing for watcher",
                  watcher[COL_NAME], watcher_name)
            self.assertEqual(appApi.remove_all_events(watcher), RET_OK)
            self.assertEqual(
                appApi.remove_watcher_by_name(watcher_name), RET_OK)


def run_tests():
    print("Running Event test")
    unittest.main(module='test.test_event', exit=True, verbosity=10)
