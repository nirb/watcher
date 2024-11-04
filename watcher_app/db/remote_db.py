import requests
from helpers.debug import print_debug


class RemoteDb:
    def __init__(self) -> None:
        self.api_url = "https://fbjtxeweu9.execute-api.us-west-2.amazonaws.com/aiaiaiai/ailogger-db-func"

    def get_table(self, table_name):
        call_url = self.api_url + f"?table_name={table_name}"
        response = requests.get(call_url)
        return response.json()

    def get_row(self, table_name, row_id):
        call_url = self.api_url + f"?table_name={table_name}&Key={row_id}"
        response = requests.get(call_url)
        return response.json()

    def add_row(self, table_name, row):
        data = {
            "table_name": table_name,
            "operation": "create",
            "payload": {"Item": row}
        }

        response = requests.post(self.api_url, json=data)

        if response.status_code == 200:
            print_debug(f"{row=} added to {table_name=}.")
            return 0
        print(f"!!! failed to add {row=} to {table_name=}.")
        print(f"!!! {response.text=}")
        return -1

    def update_row(self, table_name, payload):
        data = {
            "table_name": table_name,
            "operation": "update",
            "payload": payload
        }

        response = requests.post(self.api_url, json=data)

        if response.status_code == 200:
            print_debug(f"event in {table_name=} updated.")
            return 0
        print(f"!!! failed to update row in {table_name=}.")
        print(f"!!! {response.text=}")
        return -1

    def remove_row(self, table_name, key):
        row_id = key["id"]
        print_debug(f"deleting id {row_id}...")
        delete_row = {
            "table_name": table_name,
            "operation": "delete",
            "payload": {"Key": key}
        }
        rsp = requests.post(self.api_url, json=delete_row)
        print_debug(f"delete rsp {rsp.status_code}")
        if rsp.status_code == 200:
            print(f"{row_id=} deleted successfully from {table_name=}.")
            return 0
        else:
            print(f"{row_id=} deleted failed.")
            return -1
