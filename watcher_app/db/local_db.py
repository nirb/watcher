import boto3
import boto3.exceptions
from helpers.debug import print_debug


class LocalDb:
    def __init__(self, tables_names) -> None:
        print_debug("starting LocalDb for table", tables_names)
        self.db_type = 'dynamodb'
        self.endpoint_url = 'http://localhost:8000'
        self.db = boto3.resource(self.db_type, endpoint_url=self.endpoint_url)
        for t in tables_names:
            self.create_table(t)

    def tables_names(self):
        client = boto3.client(self.db_type, endpoint_url=self.endpoint_url)
        response = client.list_tables()
        return response["TableNames"]

    def get_table(self, table_name):
        table = self.db.Table(table_name)
        response = table.scan()
        # print_debug(f"get_table read response {response}")
        data = response['Items']
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])
        return data

    def get_row(self, table_name, row_id):
        table = self.db.Table(table_name)
        return table.get_item(Key=row_id)

    def add_row(self, table_name, row):
        print_debug(f"add_row {table_name=} {row=}")
        try:
            self.db.Table(table_name).put_item(Item=row)
            return 0
        except Exception as e:
            print(f"!!! failed to add {row=} to {table_name=}.")
            print(f"!!! {e=}")
            return -1

    def update_row(self, table_name, payload):
        print_debug(f"update_row {table_name=}")
        try:
            self.db.Table(table_name).update_item(**{k: payload[k] for k in ['Key', 'UpdateExpression',
                                                                             'ExpressionAttributeNames', 'ExpressionAttributeValues'] if k in payload})
            return 0
        except Exception as e:
            print(f"!!! failed to update row to {table_name=}.")
            return -1

    def remove_row(self, table_name, key):
        try:
            print_debug(f"Removing row with id {key['id']} from {table_name}")
            self.db.Table(table_name).delete_item(Key=key)
            return 0
        except Exception as e:
            print(f"!!! failed to delete row {key=} to {table_name=}.")
            print(f"!!! {e=}")
            return -1

    def create_table(self, table_name):
        if table_name not in self.tables_names():
            table = self.db.create_table(
                TableName=table_name,
                KeySchema=[
                    {
                        'AttributeName': 'id',
                        'KeyType': 'HASH'
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'id',
                        'AttributeType': 'S'
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
