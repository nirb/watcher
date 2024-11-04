from ..helpers.defs import *
from ..helpers.debug import print_debug, get_debug_mode


# TODO delete the file

class DynamoApi:
    def __init__(self, db) -> None:
        self.db = db

    # GENERAL TABLE FUNCTIONS

    def add_row(self, table_name, row, rows):
        if COL_NAME in row:
            row_name = row[COL_NAME]
            if len(row_name) < 3:
                print("row name is too short")
                return -1

            # check for name duplication
            if len(list(filter(lambda item: item[COL_NAME] == row_name, rows))) != 0:
                print(f"Row with name '{row_name}' already exists.")
                return -1

        return self.db.add_row(table_name, row)

    def update_row(self, table_name, payload):
        return self.db.update_row(table_name, payload)

    def remove_row_from_table(self, table_name, key):
        return self.db.remove_row(table_name, key)

    def get_row_by_id(self, id, rows):
        index = self.get_row_index_by_col(COL_ID, id, rows)
        if index != -1:
            return rows[index]
        return -1
