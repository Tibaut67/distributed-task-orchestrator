import os
import boto3
from botocore.exceptions import ClientError

# Initializes and returns a boto3 DynamoDB resource configured for the target AWS region
def get_dynamo_resource():
    return boto3.resource(
        "dynamodb",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )

# Handles all DynamoDB state persistence and status transitions for tasks
class TaskStateRepository:
    # Connects to the target DynamoDB table using the provided name or environment variable default
    def __init__(self, table_name: str | None = None):
        self.table_name = table_name or os.getenv("DYNAMODB_TABLE_NAME", "TaskStateTable")
        self._dynamo = get_dynamo_resource()
        self.table = self._dynamo.Table(self.table_name)

    # Inserts a new PENDING task into DynamoDB using a conditional write to enforce idempotency
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

    # Fetches and returns a task dictionary by task_id from DynamoDB, or None if not found
    def get_task(self, task_id: str) -> dict | None:
        response = self.table.get_item(Key={"task_id": task_id})
        return response.get("Item")

    # Updates an existing task's status attribute (e.g., PROCESSING, COMPLETED, FAILED) in DynamoDB
    def update_task_status(self, task_id: str, status: str) -> bool:
        try:
            self.table.update_item(
                Key={"task_id": task_id},
                UpdateExpression="SET #s = :status",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":status": status},
            )
            return True
        except ClientError as e:
            raise e