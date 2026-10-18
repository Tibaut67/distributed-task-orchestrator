import os
import boto3
from botocore.exceptions import ClientError

def get_dynamo_resource():
    return boto3.resource(
        "dynamodb",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

class TaskStateRepository:
    def __init__(self, table_name: str | None = None):
        self.table_name = table_name or os.getenv("DYNAMODB_TABLE_NAME", "TaskStateTable")
        self._dynamo = get_dynamo_resource()
        self.table = self._dynamo.Table(self.table_name)

    def create_task(self, task_id: str, payload: dict) -> bool:
        """
        Creates a task record.
        attribute_not_exists ensures idempotency: if task_id already exists, it fails.
        """
        try:
            self.table.put_item(
                Item={
                    "task_id": task_id,
                    "status": "PENDING",
                    "payload": payload,
                },
                ConditionExpression="attribute_not_exists(task_id)"
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise e

    def get_task(self, task_id: str) -> dict | None:
        response = self.table.get_item(Key={"task_id": task_id})
        return response.get("Item")