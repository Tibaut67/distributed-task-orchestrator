import json
from src.core.queue import TaskQueueProducer
from fastapi.testclient import TestClient
from src.api.main import app

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

def test_submit_task_endpoint_success(task_repository, sqs_queue, monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", sqs_queue["url"])

    client = TestClient(app)
    response = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert response.json() == {"task_id": "task-456", "status": "PENDING", "message": "Task accepted"}
    assert task_repository.get_task("task-456") is not None

def test_submit_task_endpoint_duplicate(task_repository, sqs_queue, monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", sqs_queue["url"])

    client = TestClient(app)
    status = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert status.status_code == 202
    status2 = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert status2.status_code == 409
    assert status2.json()["detail"] == "Task ID already exists"
