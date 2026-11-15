import os
import json
import signal
import boto3
from botocore.exceptions import ClientError
from src.core.dynamodb import TaskStateRepository
from src.core.exceptions import TaskExecutionError


# Polls SQS for up to 10 messages, transitions DynamoDB state, and handles permanent vs transient errors
def process_tasks(repo: TaskStateRepository, sqs, queue_url: str,wait_time: int = 0 ) -> int:
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10,WaitTimeSeconds=wait_time)
    messages = response.get("Messages", [])
    count = 0
    for msg in messages: #loops through messages
        count += 1
        task_id = None
        receipt_handle = msg["ReceiptHandle"]

        try:
            #parses message body and updates task status
            body = json.loads(msg["Body"])
            task_id = body["task_id"]
            payload = body["payload"]
            repo.update_task_status(task_id, "PROCESSING")

            if payload.get("force_fail"):
                raise TaskExecutionError("Simulated failure")

            repo.update_task_status(task_id, "COMPLETED")
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        except (TaskExecutionError, KeyError, json.JSONDecodeError):
            if task_id is not None:
                repo.update_task_status(task_id, "FAILED")
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

        except ClientError:
            # Transient AWS failure: leave message in SQS to retry after visibility timeout
            continue
    return count

# Manages the continuous background worker lifecycle and handles OS shutdown signals gracefully
class WorkerDaemon:
    # Initializes dependencies, running flag, and binds OS stop signals (SIGINT, SIGTERM)
    def __init__(self, repo: TaskStateRepository, sqs, queue_url: str, wait_time: int = 20):
        self.repo = repo
        self.sqs = sqs
        self.queue_url = queue_url
        self.wait_time = wait_time
        self.running = True
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

    # Flips running flag to False when the container or OS requests a shutdown
    def stop(self, signum, frame):
        self.running = False

    # Continuously processes SQS batches using long polling until a shutdown signal is received
    def run(self):
        while self.running:
            process_tasks(self.repo, self.sqs, self.queue_url, self.wait_time)


if __name__ == "__main__":
    repo = TaskStateRepository()
    sqs_client = boto3.client("sqs", region_name=os.getenv("AWS_REGION", "us-east-1"))
    queue_url = os.getenv("SQS_QUEUE_URL", "")
    daemon = WorkerDaemon(repo, sqs_client, queue_url)
    daemon.run()