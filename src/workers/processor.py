import json
from botocore.exceptions import ClientError
from src.core.dynamodb import TaskStateRepository
from src.core.exceptions import TaskExecutionError

def process_tasks(repo: TaskStateRepository, sqs, queue_url: str) -> int:
    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10)
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