import os
import boto3
import json

class TaskQueueProducer:
    def __init__(self, queue_url: str | None = None) -> None:
        self.queue_url = os.getenv("SQS_QUEUE_URL", "") or queue_url
        self.client = boto3.client("sqs",region_name=os.getenv("AWS_REGION", "us-east-1"))

    def send_task(self, task_id: str, payload: dict) -> str:
        response = self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps({"task_id": task_id, "payload": payload})
        )
        return response["MessageId"]