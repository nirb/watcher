import numpy as np
from helpers.defs import *
from helpers.helpers import DecimalEncoder, get_months_list, date_to_month_str
from helpers.debug import print_debug
from datetime import datetime
from scipy.optimize import newton
import numpy_financial as npf
import json


def to_percent(value):
    """Convert a decimal value to a percentage string."""
    return f"{value:.2f}%" if value is not None else "N/A"


def calculate_investment_profit(invested, currrent_value):
    return currrent_value - invested


def months_between_dates(date1, date2):
    if type(date1) == type("nir"):  # if its in str
        date1 = datetime.strptime(date1, DATE_FORMAT)
        date2 = datetime.strptime(date2, DATE_FORMAT)

    if date1 > date2:
        date1, date2 = date2, date1

    return (date2.year - date1.year) * 12 + (date2.month - date1.month)


def calculate_investment_info(events):
    """
    Calculate key financial information including YTD, ITD, IRR, and XIRR from a list of investment events.

    :param events: List of dictionaries. Each dictionary represents an event with keys 'COL_DATE', 'COL_TYPE', and 'COL_VALUE'.
    :return: Dictionary containing the financial summary.
    """

    # Sorting events based on date, assuming date is in DATE_FORMAT
    # events.sort(key=lambda x: datetime.strptime(x[COL_DATE], DATE_FORMAT))
    # print(json.dumps(events, indent=4, cls=DecimalEncoder))
    total_invested = 0
    total_distributed = 0
    current_value = 0

    cash_flows = []  # List to store cash flows for IRR and XIRR calculation
    cash_flow_dates = []  # Corresponding dates for each cash flow

    # Get the current year for YTD calculations
    last_event_date = datetime.strptime(events[0][COL_DATE], DATE_FORMAT)

    ytd_invested = 0
    ytd_distributed = 0

    ytd_start_value = 0
    ytd_end_value = 0
    total_commitment = 0
    for event in events:
        event_date = datetime.strptime(event[COL_DATE], DATE_FORMAT)
        event_year = event_date.year
        event_type = event[COL_TYPE]
        value = int(event[COL_VALUE])

        if event_type == STATEMENT_EVENT_TYPE:
            if current_value == 0:
                current_value = value
            # TODO think about this
            # if event_year == current_year-1:
            #    ytd_start_value = value
            if event_year == last_event_date.year:
                ytd_start_value = value
            if event_year == last_event_date.year and ytd_end_value == 0:
                ytd_end_value = value
        elif event_type == WIRE_RECEIPT_EVENT_TYPE:
            total_invested += value
            cash_flows.append(-value)  # Investment is a negative cash flow
            cash_flow_dates.append(event_date)
            if event_year == last_event_date.year:
                ytd_invested += value
        elif event_type == DISTRIBUTION_EVENT_TYPE:
            total_distributed += value
            cash_flows.append(value)  # Distribution is a positive cash flow
            cash_flow_dates.append(event_date)
            if event_year == last_event_date.year:
                ytd_distributed += value
        elif event_type == COMMITMENT_EVENT_TYPE:
            total_commitment += value

    # Add the current value of the investment as the final cash flow (assuming the latest date)
    if current_value:
        cash_flows.append(current_value)
        cash_flow_dates.append(last_event_date)

    # Calculate Net Gain or Loss
    net_gain_or_loss = current_value + total_distributed - total_invested

    # Calculate ROI (Return on Investment) as a percentage
    roi = (net_gain_or_loss / total_invested) * \
        100 if total_invested > 0 else 0

    # Calculate YTD Net Gain or Loss
    print_debug(
        f"{ytd_end_value=} {ytd_start_value=} {ytd_distributed=} {ytd_invested=}")
    ytd_net_gain_or_loss = ytd_end_value - ytd_invested + \
        ytd_distributed - ytd_start_value

    # Calculate YTD as a percentage
    ytd_start = ytd_start_value + ytd_distributed + ytd_invested
    print_debug(f"{ytd_start=} {ytd_net_gain_or_loss=}")
    ytd_percentage = 0 if ytd_start == 0 else 100 * \
        (ytd_net_gain_or_loss / ytd_start)
    print_debug(f"{ytd_percentage=}")

    # Calculate ITD (Inception-to-Date) Net Gain or Loss
    itd_net_gain_or_loss = net_gain_or_loss

    # Calculate ITD as a percentage
    itd_percentage = (itd_net_gain_or_loss / total_invested) * \
        100 if total_invested > 0 else 0

    # Calculate IRR using numpy (requires periodic cash flows)
    irr = npf.irr(cash_flows) * 100 if cash_flows else 0

    # Calculate XIRR using actual dates (requires uneven cash flows)
    def calculate_xirr(cash_flows, cash_flow_dates):
        """ Calculate the XIRR using cash flows and their corresponding dates. """
        def xnpv(rate, cash_flows, cash_flow_dates):
            return sum(cf / (1 + rate) ** ((d - cash_flow_dates[0]).days / 365) for cf, d in zip(cash_flows, cash_flow_dates))

        def xirr(cash_flows, cash_flow_dates, guess=0.1):
            return newton(lambda r: xnpv(r, cash_flows, cash_flow_dates), guess)

        return xirr(cash_flows, cash_flow_dates) * 100 if cash_flows else 0
    try:
        xirr = calculate_xirr(cash_flows, cash_flow_dates)
    except Exception as e:
        xirr = 0

    invested_months = 0
    if len(events) > 1:
        invested_months = months_between_dates(
            events[0][COL_DATE], events[-1][COL_DATE])
    # Prepare the result dictionary
    result = {
        COL_INVESTED: total_invested,
        COL_COMMITMENT: total_commitment,
        COL_UNFUNDED: total_invested - total_commitment,
        COL_DIST_ITD: total_distributed,
        COL_DIST_YTD: ytd_distributed,
        COL_VALUE: current_value,
        ROI: to_percent(roi),
        COL_PROFIT_YTD: ytd_net_gain_or_loss,
        COL_PROFIT_ITD: itd_net_gain_or_loss,
        NET_GAIN: net_gain_or_loss,
        YTDP: to_percent(ytd_percentage),
        ITDP: to_percent(itd_percentage),
        IRR: to_percent(irr),
        XIRR: to_percent(xirr),
        MONTHS: invested_months
    }

    # print(json.dumps(result, indent=4))

    return result


def generate_year_row():
    year_row = {}
    for m in get_months_list():
        year_row[m] = 0

    return year_row


def get_events_months(events):

    months = []
    for year in range(2022, 2025):
        months += get_months_list(year)

    print(json.dumps(months, indent=2, cls=DecimalEncoder))
    return

    first_date = event_date = datetime.strptime(
        events[-1][COL_DATE], DATE_FORMAT)
    for e in reversed(events):
        event_date = datetime.strptime(e[COL_DATE], DATE_FORMAT)
        months[f"{event_date.year}:{event_date.month}"] = int(e[COL_VALUE])

        month = date_to_month_str(event_date)
        if years[event_date.year][month] == 0:
            years[event_date.year][month] = e[COL_VALUE]
        print(e[COL_VALUE], e[COL_DATE], e[COL_TYPE], event_date.month)
    print(json.dumps(years, indent=2, cls=DecimalEncoder))
