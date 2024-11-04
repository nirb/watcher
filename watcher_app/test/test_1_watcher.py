import unittest
from api.api import AppApi
from helpers.defs import *
from test.helper import rand_from_list, number_of_watchers, COMITTED, generate_watcher, NUMBER_OF_WATCHERS, test_function_printer

appApi = AppApi(local_db=True, test_mode=True)

COMITTED_UPDATE = 1234


class TestWatchers(unittest.TestCase):
    @test_function_printer
    def test_1_1_start(self):
        self.test_cleanup(show=False)
        self.assertEqual(number_of_watchers(appApi), 0)

    @test_function_printer
    def test_1_2_add_watchers(self):
        for x in range(NUMBER_OF_WATCHERS):
            self.assertEqual(appApi.add_watcher(generate_watcher(appApi)), 0)

    @test_function_printer
    def test_1_3_update(self):
        for index, name in enumerate(appApi.get_watcher_names()):
            watcher = appApi.get_watcher_by_name(name)
            watcher[COL_NAME] += "-updateed"
            watcher[COL_COMMITMENT] = COMITTED_UPDATE+index
            watcher[COL_UNFUNDED] = COMITTED_UPDATE*index
            self.assertEqual(appApi.update_watcher(watcher), 0)

    @test_function_printer
    def test_1_4_check_update(self):
        for index, name in enumerate(appApi.get_watcher_names()):
            watcher = appApi.get_watcher_by_name(name)
            self.assertEqual(watcher[COL_COMMITMENT], COMITTED_UPDATE+index)
            self.assertEqual(watcher[COL_UNFUNDED], COMITTED_UPDATE*index)

    @test_function_printer
    def test_1_5_remove_watcher_by_name(self):
        self.show()
        self.remove_watcher()
        self.remove_watcher()

    @test_function_printer
    def remove_watcher(self):
        number_of_watchers_start = number_of_watchers(appApi)
        name_to_remove = rand_from_list(appApi.get_watcher_names())
        self.assertEqual(appApi.remove_watcher_by_name(name_to_remove), 0)
        self.assertEqual(number_of_watchers_start-1,
                         number_of_watchers(appApi))

    @test_function_printer
    def test_cleanup(self, show=True):
        self.show(show)
        # remove all events and wathcers
        for watcher_name in appApi.get_watcher_names():
            watcher = appApi.get_watcher_by_name(watcher_name)
            self.assertEqual(appApi.remove_all_events(watcher), 0)
            self.assertEqual(appApi.remove_watcher_by_name(watcher_name), 0)

    @test_function_printer
    def show(self, show=True):
        if show:
            appApi.show_watchers()


def run_tests():
    unittest.main(module='test.test_watcher', exit=True, verbosity=10)
