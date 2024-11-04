import numpy as np
from helpers.defs import *
from helpers.helpers import DecimalEncoder, int_to_str
from datetime import datetime
from scipy.optimize import newton
import numpy_financial as npf
import json


def to_percent(value):
    """Convert a decimal value to a percentage string."""
    return f"{value:.2f}%" if value is not None else "N/A"


def calculate_investment_profit(invested, currrent_value):
    return currrent_value - invested


def calculate_investment_info(events):
    """
    Calculate key financial information including YTD, ITD, IRR, and XIRR from a list of investment events.

    :param events: List of dictionaries. Each dictionary represents an event with keys 'COL_DATE', 'COL_TYPE', and 'COL_VALUE'.
    :return: Dictionary containing the financial summary.
    """

    # Sorting events based on date, assuming date is in DATE_FORMAT
    events.sort(key=lambda x: datetime.strptime(x[COL_DATE], DATE_FORMAT))
    # print(json.dumps(events, indent=4, cls=DecimalEncoder))
    total_invested = 0
    total_distributed = 0
    current_value = 0

    cash_flows = []  # List to store cash flows for IRR and XIRR calculation
    cash_flow_dates = []  # Corresponding dates for each cash flow

    # Get the current year for YTD calculations
    now = datetime.now()
    current_year = now.year
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
            current_value = value
            if event_year == current_year-1:
                ytd_start_value = value
            if event_year == current_year and ytd_start_value == 0:
                ytd_start_value = value
            if event_year == current_year:
                ytd_end_value = value
        elif event_type == WIRE_RECEIPT_EVENT_TYPE:
            total_invested += value
            cash_flows.append(-value)  # Investment is a negative cash flow
            cash_flow_dates.append(event_date)
            if event_date.year == current_year:
                ytd_invested += value
        elif event_type == DISTRIBUTION_EVENT_TYPE:
            total_distributed += value
            cash_flows.append(value)  # Distribution is a positive cash flow
            cash_flow_dates.append(event_date)

            if event_date.year == current_year:
                ytd_distributed += value
        elif event_type == COMMITMENT_EVENT_TYPE:
            total_commitment += value

    # Add the current value of the investment as the final cash flow (assuming the latest date)
    if current_value:
        cash_flows.append(current_value)
        cash_flow_dates.append(now)

    # Calculate Net Gain or Loss
    net_gain_or_loss = current_value + total_distributed - total_invested

    # Calculate ROI (Return on Investment) as a percentage
    roi = (net_gain_or_loss / total_invested) * \
        100 if total_invested > 0 else 0

    # Calculate YTD Net Gain or Loss
    ytd_net_gain_or_loss = ytd_end_value - \
        ytd_start_value + ytd_distributed - ytd_invested

    # Calculate YTD as a percentage
    ytd_start = ytd_start_value + ytd_distributed - ytd_invested
    ytd_percentage = 0 if ytd_start == 0 else 100 * \
        (ytd_net_gain_or_loss / ytd_start)

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

    # Prepare the result dictionary
    result = {
        COL_INVESTED: total_invested,
        COL_COMMITMENT: total_commitment,
        COL_UNFUNDED: total_invested - total_commitment,
        "Distribution_ITD": total_distributed,
        "Distribution_YTD": ytd_distributed,
        COL_VALUE: current_value,
        "Net Gain or Loss": net_gain_or_loss,
        ROI: to_percent(roi),
        COL_PROFIT_YTD: ytd_net_gain_or_loss,
        "YTD%": to_percent(ytd_percentage),
        "ITD": itd_net_gain_or_loss,
        "ITD%": to_percent(itd_percentage),
        "IRR": to_percent(irr),
        "XIRR": to_percent(xirr)
    }

    # print(json.dumps(result, indent=4))

    return result


# Example usage
events = [
    {COL_DATE: "2023-01-01", COL_TYPE: WIRE_RECEIPT_EVENT_TYPE, COL_VALUE: 4000},
    {COL_DATE: "2023-02-15", COL_TYPE: WIRE_RECEIPT_EVENT_TYPE, COL_VALUE: 1000},
    {COL_DATE: "2023-05-10", COL_TYPE: DISTRIBUTION_EVENT_TYPE, COL_VALUE: 1000},
    {COL_DATE: "2023-02-28", COL_TYPE: STATEMENT_EVENT_TYPE, COL_VALUE: 5400},
    {COL_DATE: "2024-02-28", COL_TYPE: STATEMENT_EVENT_TYPE, COL_VALUE: 5500},
    {COL_DATE: "2024-02-28", COL_TYPE: DISTRIBUTION_EVENT_TYPE, COL_VALUE: 100},
    {COL_DATE: "2024-09-30", COL_TYPE: STATEMENT_EVENT_TYPE, COL_VALUE: 6000},
]

# calculate_investment_info(events)
