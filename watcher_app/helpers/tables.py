from helpers.debug import print_debug, get_debug_mode
from helpers.defs import *


def get_row_index_by_col(col_name: str, col_value: any, rows: list):
    if len(rows) == 0:
        print_debug(
            f"get_row_index_by_col empty {rows=}")
        return -1
    index = next((i for i, item in enumerate(rows)
                  if item[col_name] == col_value), -1)

    if get_debug_mode() == True:
        debug_rows = [{f"{col_name}": r[col_name]} for r in rows]

        print_debug(
            f"get_row_index_by_col {col_name=} {col_value=} {debug_rows=}")
        print_debug(f"get_row_index_by_col {index=}")
    return index


def get_row_by_name(name, rows):
    if len(rows) == 0:
        return -1
    index = get_row_index_by_col(COL_NAME, name, rows)
    if index != -1:
        return rows[index]
    return -1
