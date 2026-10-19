import json
from src.core.queue import TaskQueueProducer

def test_create_task_success(task_repository):
    created = task_repository.create_task("task-123", {"action": "process"})
    assert created is True

    item = task_repository.get_task("task-123")
    assert item is not None
    assert item["status"] == "PENDING"
    assert item["payload"] == {"action": "process"}


def test_create_task_duplicate_idempotency(task_repository):
    first_attempt = task_repository.create_task("task-123", {"data": "first"})
    second_attempt = task_repository.create_task("task-123", {"data": "second"})

    assert first_attempt is True
    assert second_attempt is False

def test_send_task_to_sqs_success(sqs_queue) -> None:
    producer = TaskQueueProducer(queue_url=sqs_queue["url"])
    msg_id = producer.send_task("task-456", {"metric": "latency"})
    assert isinstance(msg_id, str) and len(msg_id) > 0

    res = sqs_queue["client"].receive_message(QueueUrl = sqs_queue["url"], MaxNumberOfMessages = 1)
    assert "Messages" in res
    body = json.loads(res["Messages"][0]["Body"])
    assert body["task_id"] == "task-456"
    assert body["payload"]["metric"] == "latency"