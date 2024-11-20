from random import randint
from test.test import run_tests
from ai.ai import analyze_doc
from ui.plots import Plot
from helpers.investment_calc import calculate_investment_profit, calculate_investment_info
import sys
import os
import json
from simple_term_menu import TerminalMenu
from datetime import datetime
from dotenv import load_dotenv

from api.api import AppApi
from helpers.defs import *
from helpers.debug import get_debug_mode, toggle_debug_mode, print_debug
from helpers.helpers import currency_to_symbol_or_type, DecimalEncoder, get_months_list, \
    date_to_month_str, int_to_str


load_dotenv()
appApi = AppApi(local_db=False)


def select_from_list(message, input_list, current_selection=""):
    if len(input_list) == 0:
        print(" not found")
        return None
    current_text = "" if current_selection == "" else f"(current: {current_selection})"

    print(f"{message} {current_text}:", flush=True)
    show_list = input_list.copy()
    show_list.append(BACK_TO_MAIN_MENU)
    show_list = [f"[{index}] {item}" for index, item in enumerate(input_list)]
    menu = TerminalMenu(show_list)
    selected = input_list[menu.show()]
    if selected == BACK_TO_MAIN_MENU:
        back_to_main_menu()
    print(selected)
    return selected


def select_currency(current_selection=""):
    return select_from_list(f"Currency", CURRENCY_TYPES, current_selection)


def select_watcher_type(current_selection=""):
    return select_from_list("Watcher Type", WATCHER_TYPES, current_selection)


def select_event_type(types_list, current_selection=""):
    if len(types_list) == 1:
        return types_list[0]
    return select_from_list("Event Type", types_list, current_selection)


def select_watcher():
    return select_from_list("Watcher", appApi.get_watcher_names())


def select_int_input(msg, default_value):
    while True:
        value_str = input(msg)
        if value_str == "" and default_value is not None:
            return default_value
        else:
            try:
                return int(value_str)
            except Exception as e:
                print("Commitment must be a valid number")


def add_event_menu():
    selected_watcher = select_watcher()
    watcher = appApi.get_watcher_by_name(selected_watcher)
    if not watcher:
        print(f"Watcher {selected_watcher} not dound")
        return
    if watcher[COL_TYPE] in INVESTMENT_WATCHER_TYPES:
        event_type = select_event_type(INVESTMENT_EVENT_TYPES)
        value = int(input("Enter value: "))
    else:
        value = 0
        event_type = select_event_type(OTHER_EVENT_TYPES)

    while True:
        date = input("Enter date (YYYY-MM-DD /enter for today): ")
        if date == "":
            date = datetime.now().strftime(DATE_FORMAT)
            break
        else:  # validate input date
            try:
                datetime.strptime(date, DATE_FORMAT).date()
                break
            except:
                print("Error in date formate")

    description_default = f"{event_type}"
    description = input(
        f"Enter description / enter for '{description_default}':")

    if description == "":
        description = description_default

    ret = appApi.add_event(
        watcher=watcher, date=date, type=event_type,
        value=value, description=description)
    print(f"Add {event_type} event succeddded." if ret ==
          RET_OK else f"Add {event_type} event Failed!!!!")
    if event_type == COMMITMENT_EVENT_TYPE:
        if are_you_sure("Do you want to add initial statement with value 0"):
            ret = appApi.add_event(
                watcher=watcher, date=date, type=STATEMENT_EVENT_TYPE,
                value=0, description="initial statement")
            print(f"Add {STATEMENT_EVENT_TYPE} event succeddded." if ret ==
                  RET_OK else f"Add {STATEMENT_EVENT_TYPE} event Failed!!!!")


def select_event_menu():
    watcher = appApi.get_watcher_by_name(select_watcher())
    # appApi.show_events(watcher)
    watcher_info = appApi.get_watcher_info(watcher)
    if watcher_info:
        options = [str(event[COL_DATE]) + "-" + str(event[COL_VALUE]) + "-" + event[COL_DESCRIPTION]
                   for event in watcher_info[COL_EVENTS]]
        selected = select_from_list("Select Event", options)
        if selected:
            event = watcher_info["events"][options.index(selected)]
            print("Selected event id", event[COL_ID])
            return event, watcher

    return None, None


def update_event_menu():
    event, watcher = select_event_menu()
    if event == None:
        return
    date = input(f"Enter date ({str(event[COL_DATE])}): ")
    if date == "":
        date = event[COL_DATE]

    value = 0
    if watcher[COL_TYPE] in INVESTMENT_WATCHER_TYPES:
        # type = select_event_type(INVESTMENT_EVENT_TYPES)
        input_value = input(f"Enter value: ({event[COL_VALUE]}): ")
        if input_value == "":
            value = int(event[COL_VALUE])
        else:
            value = int(input_value)
    else:
        # type = select_event_type(OTHER_EVENT_TYPES)
        pass
    event_type = event[COL_TYPE]
    description = input(f"Enter description: ({event[COL_DESCRIPTION]}): ")
    if description == "":
        description = event[COL_DESCRIPTION]
    appApi.update_event(parent_id=watcher[COL_ID], event_id=event[COL_ID],
                        date=date, event_type=event_type,
                        value=value, description=description)


def update_watcher_menu():
    watcher = appApi.get_watcher_by_name(select_watcher())
    watcher_name = input(f"Watcher name ({watcher[COL_NAME]}): ")
    if watcher_name != "":
        watcher[COL_NAME] = watcher_name

    watcher[COL_CURRENCY] = select_currency(
        current_selection=watcher[COL_CURRENCY])
    watcher[COL_TYPE] = select_watcher_type(
        current_selection=watcher[COL_TYPE])
    watcher[COL_ACTIVE] = select_from_list("Active?", ["YES", "NO"])
    appApi.update_watcher(watcher)


def remove_event_menu():
    event, watcher = select_event_menu()
    if event:
        if appApi.remove_event(event[COL_ID]) == 0:
            print(
                f"remove event {event[COL_ID]} from watcher '{watcher[COL_NAME]}' succedded")
        else:
            print(f"failed to remove event from watcher '{watcher[COL_NAME]}'")


def add_watcher_investment_cols(watcher):
    ret_watcher = watcher
    if watcher[COL_TYPE] in INVESTMENT_WATCHER_TYPES:
        current_text = f"Current {watcher[COL_COMMITMENT]}" if COL_COMMITMENT in watcher else ""
        default_value = watcher[COL_COMMITMENT] if COL_COMMITMENT in watcher else None
        commitment = select_int_input(
            f"Investment Commitment {current_text}:", default_value)
        current_text = f"Current {watcher[COL_UNFUNDED]}" if COL_UNFUNDED in watcher else ""
        default_value = watcher[COL_UNFUNDED] if COL_UNFUNDED in watcher else None
        unfunded = select_int_input(
            f"Unfunded {current_text}:", default_value)
    else:
        commitment = 0
        unfunded = 0
    ret_watcher[COL_COMMITMENT] = commitment
    ret_watcher[COL_UNFUNDED] = unfunded
    return ret_watcher


def add_watcher_menu(name=None):
    if name == None:
        name = input("Watcher name: ")
    if len(name) < 3:
        print("Watcher name is too short")
        return
    type = select_watcher_type()
    watcher = {COL_TYPE: type, COL_NAME: name, COL_ACTIVE: "YES"}
    if type in INVESTMENT_WATCHER_TYPES:
        watcher[COL_CURRENCY] = select_currency()
        # watcher = add_watcher_investment_cols(watcher)
    else:
        watcher[COL_CURRENCY] = "NA"

    advisors = appApi.get_advisors()
    advisor_name = select_from_list("Select Advisor",
                                    list(map(lambda item: item[COL_ID], advisors)))
    watcher[ADVISOR_NAME] = advisor_name
    if appApi.add_watcher(watcher):
        print(f"New Watcher added {name}")


def show_events_menu():
    selected_watcher = select_watcher()
    if selected_watcher:
        watcher = appApi.get_watcher_by_name(selected_watcher)
        if watcher:
            print("Events:")
            show_events(watcher)
        else:
            print(f"Watcher {selected_watcher} not dound")


def are_you_sure(message):
    random_list = [NO for i in range(5)]
    random_list[randint(1, len(random_list)-1)] = YES
    return select_from_list(message, random_list) == YES


def remove_watcher_menu():
    watcher_name = select_watcher()
    if are_you_sure(f"Are you sure ???? !!!!! deleting {watcher_name=}"):
        if appApi.remove_watcher_by_name(watcher_name) == RET_OK:
            print(f"'{watcher_name}' removed.")
        else:
            print(
                f"Failed to remove '{watcher_name}', check if watcher has events")


def remove_events_menu():
    print("Removing Events for")
    watcher = appApi.get_watcher_by_name(select_watcher())

    if are_you_sure(f"Are you sure ???? !!!!! deleting all '{watcher[COL_NAME]}' events?"):
        appApi.remove_all_events(watcher)


def watcher_graph():
    watcher = appApi.get_watcher_by_name(select_watcher())
    if watcher != -1:
        watcher_info = appApi.get_watcher_info(watcher)
        statements = list(filter(
            lambda item: item[COL_TYPE] == STATEMENT_EVENT_TYPE, watcher_info["events"]))
        distributions = list(filter(
            lambda item: item[COL_TYPE] == DISTRIBUTION_EVENT_TYPE, watcher_info["events"]))
        currency = currency_to_symbol_or_type(watcher[COL_CURRENCY])
        plots_data = [{"data": statements,
                       "title": STATEMENT_EVENT_TYPE,
                       "currency": currency}]
        if len(distributions) > 0:
            plots_data.append(
                {"data": distributions,
                 "title": DISTRIBUTION_EVENT_TYPE,
                 "currency": currency})
            Plot().show_plots(plots_data, window_title=watcher[COL_NAME])
        else:
            Plot().show_plot(list(reversed(plots_data[0]["data"])),
                             plot_title=STATEMENT_EVENT_TYPE,
                             currency=currency, window_title=watcher[COL_NAME])


def show_watcher_info(watcher=None, watcher_name=None, selected_year=None):
    if watcher is None and watcher_name is not None:
        watcher = appApi.get_watcher_by_name(watcher_name)

    events = appApi.get_watcher_events(watcher, fill_dates=True)
    if selected_year != None:
        events = list(filter(lambda e: datetime.strptime(
            e[COL_DATE], DATE_FORMAT).year == selected_year, events))

    start_year = datetime.strptime(events[0][COL_DATE], DATE_FORMAT).year
    row = {"Year": start_year}
    rows = [row]
    values_in_k = False
    for event in events:
        if event[COL_TYPE] == STATEMENT_EVENT_TYPE:
            event_date = datetime.strptime(
                event[COL_DATE], DATE_FORMAT)
            if event_date.year != start_year:
                row = {"Year": event_date.year}
                start_year = event_date.year
                rows.append(row)
            value = event[COL_VALUE]
            if value > 1000000:
                values_in_k = True
                value /= 1000
            row[date_to_month_str(event_date)] = int_to_str(value)

    # calculate ROI
    for row in rows:
        year = row["Year"]
        events_year = []
        for event in events:
            event_year = datetime.strptime(
                event[COL_DATE], DATE_FORMAT).year
            if event_year == year:
                events_year.append(event)
        info = calculate_investment_info(events_year)
        row["ROI"] = info[YTDP]
        row["YTD"] = info[COL_PROFIT_YTD]

    if get_debug_mode():
        for e in events:
            print(e[COL_DATE], e[COL_VALUE], e[COL_TYPE])

    info = calculate_investment_info(events)
    if get_debug_mode():
        print(json.dumps(info, indent=2, cls=DecimalEncoder))
    more_info = f"ITD:{info[ITDP]} IRR:{info[IRR]} XIRR:{info[XIRR]}"
    print(
        f'{more_info}, Values are in {"K-" if values_in_k else ""}{watcher[COL_CURRENCY]}')
    Plot().show_table(rows, headers=[
        "Year"]+get_months_list()+["ROI", "YTD"])


def watcher_info():
    watcher = appApi.get_watcher_by_name(select_watcher())
    if watcher != -1:
        show_watcher_info(watcher=watcher)


def toggle_debug():
    toggle_debug_mode()


def date_str_to_datetime(date_str):
    supported_formats = [DATE_FORMAT, "%d/%m/%Y", "%d/%m/%y",
                         "%B %d, %Y",  "%u %B %Y"]

    for formate in supported_formats:
        try:
            dt = datetime.strptime(date_str, formate)
            return dt.strftime(DATE_FORMAT)
        except Exception as e:
            continue
    print(f"Failed to format {date_str} to datetime, please improve the code")
    print(f"date_str_to_datetime in {__file__}")
    exit(0)


def clean_files_list(file_list):
    remove_files = ["analyezed", ".DS_Store"]
    for f_name in remove_files:
        if f_name in file_list:
            file_list.remove(f_name)
    return file_list


def get_watcher_name_from_json_ai(ai_json):
    if "fund_name" in ai_json:
        return ai_json["fund_name"]

    json_list_names = ["founds", "fund_details", "found"]
    for name in json_list_names:
        if name in ai_json:
            for f_json in ai_json[name]:
                if f_json["current_value"]:
                    return f_json["fund_name"]

    for f_json in ai_json:
        if f_json["current_value"]:
            return f_json["fund_name"]

    return RET_FAILED


def get_event_type_from_doc(doc_type):
    options = [("statement", STATEMENT_EVENT_TYPE),
               ("distribution", DISTRIBUTION_EVENT_TYPE),
               ("wire", WIRE_RECEIPT_EVENT_TYPE),
               ("capital call", WIRE_RECEIPT_EVENT_TYPE),
               ("commitment", COMMITMENT_EVENT_TYPE)]

    print("get_event_type_from_doc", doc_type, options)

    for option in options:
        if option[0] in doc_type.lower():
            return option[1]
    print("can't find event type from doc_type", doc_type)
    exit(0)


def ai_menu():
    # watcher_name = select_watcher()
    folder = ""  # input(f"Enter docs folder (enter {INVESTMENTS_DOC_DIR}): ")
    if folder == "":
        folder = INVESTMENTS_DOC_DIR

    files_in_directory = clean_files_list(os.listdir(folder))

    if len(files_in_directory) == 0:
        print(f"No files found in {INVESTMENTS_DOC_DIR}")
        return

    # print(files_in_directory)
    docs_types = "(statement or distribution or wire or capital call or commitment)"
    selected_doc = select_from_list("Select a doc", sorted(files_in_directory))
    distribution_ai = "return a json with the following keys \
                  (fund_name, title, current_value (the distribution, without commas), report_date,\
                      doc_type, currency, period_date)"
    statement_ai = "return a json with the following keys \
                  (fund_name, title, current_value (without commas), report_date,\
                    period_date, doc_type, initial_investment, currency)"
    wire_ai = "return a json with the following keys \
                  (fund_name, title, current_value (without commas and without dot), report_date,\
                     doc_type, currency)"
    general_ai_info = f"in most cases 'fund_name' is in the first row of the title, 'doc_type' can be on of {docs_types} and in most cases is in the title"
    general_ai_info += ", return a valid json (without comments)"
    ai_text = f"if it is a 'statement' {statement_ai},\
        if it is a 'distribution' {distribution_ai}, \
        if it is a 'wire' or 'capital call' {wire_ai}, {general_ai_info}"
    file_to_analyze = os.path.join(folder, selected_doc)
    result = analyze_doc(ai_text, file_to_analyze)
    json_index_start = result.find("```json") + len("```json")
    json_index_end = result.find("```", json_index_start+5)
    try:
        ai_json = json.loads(result[json_index_start:json_index_end-1])
    except Exception as e:
        print("load failed", e)
        print(result, json_index_start, json_index_end)
        print(result[json_index_start:json_index_end-2])
        return
    print("Ai json", json.dumps(ai_json, indent=4))
    watcher_name = get_watcher_name_from_json_ai(ai_json)
    print_debug(f"{watcher_name=}")
    if watcher_name == RET_FAILED:
        print(f"\nWatcher not found in ai return !!!")
        return

    watcher = appApi.get_watcher_by_name(watcher_name)
    if watcher == RET_FAILED:
        print(f"Watcher with name '{watcher_name}' not found.")
        selected = select_from_list(
            f"Do you want to create new watcher with the name '{watcher_name}'",
            [YES, NO, "Use exsiting"])
        if selected == YES:
            add_watcher_menu(watcher_name)
            watcher = appApi.get_watcher_by_name(watcher_name)
            if watcher == RET_FAILED:
                return
        elif selected == "Use exsiting":
            watcher_name = select_watcher()
            watcher = appApi.get_watcher_by_name(watcher_name)
        else:
            return

    event_type = get_event_type_from_doc(ai_json["doc_type"])
    if event_type == STATEMENT_EVENT_TYPE:
        date = date_str_to_datetime(ai_json["period_date"])
    else:
        date = date_str_to_datetime(ai_json["report_date"])

    value = int(ai_json["current_value"])

    print(
        f"\nAI found event for '{watcher[COL_NAME]}' with the following paramets:")
    print(f"Date:        {date}")
    print(f"Type:        {event_type}")
    print(f"Value:       {value:,} {ai_json['currency']}")

    if select_from_list("Do you want to add this event?", ["YES", "NO"]) == "NO":
        print("Event didnt added !!!")
        return

    description = input(
        "Enter description (enter for 'Auto added by ai'): ")
    if description == "":
        description = "Auto added by ai"
    print(f"Description: {description}\n\n")

    if appApi.add_event(watcher=watcher, date=date, type=event_type,
                        value=value, description=description) == RET_OK:
        move_to_dir = os.path.join(folder, "analyezed")
        if not os.path.isdir(move_to_dir):
            os.mkdir(move_to_dir)
        os.rename(file_to_analyze, os.path.join(move_to_dir, selected_doc))
        print("add event succedded")
    else:
        print("add event failed")


def back_to_main_menu():
    raise (Exception(BACK_TO_MAIN_MENU))


def show_sub_menu(menu_entries, add_back=True):
    if add_back and BACK_TO_MAIN_MENU not in menu_entries:
        menu_entries.append([BACK_TO_MAIN_MENU, back_to_main_menu])
    menu = TerminalMenu(
        [f"[{index}] {item[0]}" for index, item in enumerate(menu_entries)])
    choice = menu.show()
    menu_entries[choice][1]()


def show_watcher_summary():
    watchers = appApi.get_watchers()
    if len(watchers) > 0:
        print("Watchers summary")
        print_debug("Watchers summary", CURRENCY_TYPES, watchers)
        rows = []
        for currency in CURRENCY_TYPES:
            currency_sum = 0
            invested = 0
            ytd = 0
            commited = 0
            for w in watchers:
                if w[COL_CURRENCY] == currency:
                    watcher_info = appApi.get_watcher_info(w)
                    if watcher_info is not None:
                        print_debug(
                            f"get_watcher_info {json.dumps(watcher_info, indent=4,cls=DecimalEncoder)}")
                        currency_sum += watcher_info[COL_FINANCE][COL_VALUE]
                        invested += watcher_info[COL_FINANCE][COL_INVESTED]
                        print(
                            f"watcher {w[COL_NAME]} ITD {watcher_info[COL_FINANCE][COL_PROFIT_YTD]}")
                        ytd += watcher_info[COL_FINANCE][COL_PROFIT_YTD]
                        commited += watcher_info[COL_FINANCE][COL_COMMITMENT]
                    else:
                        print("Error watcher_info not created")

            row = {COL_CURRENCY: currency,
                   COL_VALUE: currency_sum,
                   COL_INVESTED: invested,
                   COL_PROFIT_ITD: calculate_investment_profit(invested, currency_sum),
                   COL_PROFIT_YTD: ytd,
                   COL_COMMITMENT: commited,
                   COL_UNFUNDED: invested-commited}

            rows.append(row)
        print_debug("rows", json.dumps(rows, indent=2, cls=DecimalEncoder))
        Plot().show_table(rows, headers=[
            COL_VALUE, COL_INVESTED, COL_UNFUNDED, COL_PROFIT_ITD, COL_PROFIT_YTD])


def show_watchers():
    watchers = appApi.get_watchers()
    if len(watchers) == 0:
        print("No Watchers found, create the first one")
        return

    print_debug(json.dumps(watchers, indent=4, cls=DecimalEncoder))

    show_watcher_summary()
    for w in watchers:
        watcher_info = appApi.get_watcher_info(w)
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
    headers = [COL_NAME, COL_VALUE,
               COL_INVESTED, COL_DIST_ITD, ROI, MONTHS]
    print_debug("headsers", headers)
    Plot().show_table(watchers, headers=headers)
    headers = [COL_NAME, COL_PROFIT_ITD, COL_PROFIT_YTD,
               COL_DIST_YTD, COL_UNFUNDED, XIRR]
    Plot().show_table(watchers, headers=headers)


def watchers_menu():
    show_sub_menu([
        ["Show Watchers", show_watchers],
        ["Add Watcher", add_watcher_menu],
        ["Show Watcher Graph", watcher_graph],
        ["Show Watcher Info", watcher_info],
        ["Update Watcher", update_watcher_menu],
        ["Remove Watcher", remove_watcher_menu]
    ])


def events_menu():
    show_sub_menu([
        ["Show Events", show_events_menu],
        ["Add Event", add_event_menu],
        ["Update Event", update_event_menu],
        ["Remove Event", remove_event_menu],
        ["Remove Events", remove_events_menu],
    ])


def get_string_input(question):
    selected_input = input(question)
    if len(selected_input) < 3:
        print("input is too short")
        back_to_main_menu()
    return selected_input


def add_advisor():
    advisor_name = get_string_input("Advisor name: ")
    advisor_phone_number = get_string_input("Advisor phone: ")
    advisor_mail = get_string_input("Advisor mail: ")

    if appApi.add_advisor(advisor_name, advisor_phone_number, advisor_mail) == RET_OK:
        print(f"Advisor '{advisor_name}' added sucsessfuly")
    else:
        print("Faild to add advisor")


def remove_advisor():
    advisors = appApi.get_advisors()
    if len(advisors) == 0:
        print("No advisors found")
        return
    advisor_name = select_from_list("Select Advisor",
                                    list(map(lambda item: item[COL_ID], advisors)))
    if appApi.remove_advisor(advisor_name) == RET_OK:
        print(f"Advisor '{advisor_name}' removed sucsessfuly")
    else:
        print("Faild to remove advisor")


def show_advisors():
    advisors = appApi.get_advisors()
    if len(advisors) == 0:
        print("No advisors found")
        return
    Plot().show_table(advisors, headers=[COL_ID, COL_MAIL, COL_PHONE])


def show_events(watcher):
    watcher_events = appApi.get_watcher_events(watcher)
    if len(watcher_events) > 0:
        print_debug(f"show_events {watcher_events}")
        for event_type in EVENT_TYPES:
            events = list(
                filter(lambda event: event[COL_TYPE] == event_type, watcher_events))
            if len(events) > 0:
                Plot().show_table(
                    events, value_postfix=watcher[COL_CURRENCY] if COL_CURRENCY in watcher else "")
    else:
        print("No events found for this watcher")


def settings_menu():
    debug_menu = "Disable Debug" if get_debug_mode() else "Enable Debug"
    show_sub_menu([[debug_menu, toggle_debug],
                   ["Add Advisor", add_advisor],
                   ["Remove Advisor", remove_advisor],
                   ["Show Advisors", show_advisors],
                   ["Run Tests", run_tests],
                   ])


def main_menu():
    if get_debug_mode():
        print("!!!!!! RUNNING IN DEBUG MODE !!!!")

    menu_entries = [
        ["AI", ai_menu],
        ["Watchers", watchers_menu],
        ["Events", events_menu],
        ["Settings", settings_menu],
        ["Exit", exit],
    ]
    show_sub_menu(menu_entries, add_back=False)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        del sys.argv[1]  # TODO read about test arguments
        run_tests()

    if len(sys.argv) >= 3 and sys.argv[1] == "watcher_info":
        if len(sys.argv) == 3:
            show_watcher_info(
                watcher=None, watcher_name=sys.argv[2], selected_year=None)
        else:
            show_watcher_info(
                watcher=None, watcher_name=sys.argv[2], selected_year=int(sys.argv[3]))
        exit(0)

    # watcher_info("Hazavim Bond, L.P")
    # exit(0)

    while True:
        try:
            main_menu()
        except Exception as e:
            print(e)
            if str(e) != BACK_TO_MAIN_MENU:
                raise (e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(f"exception:{e},in file:{fname}/{exc_tb.tb_lineno}")
