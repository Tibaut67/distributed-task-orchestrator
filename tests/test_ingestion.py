import json
from src.core.queue import TaskQueueProducer
from fastapi.testclient import TestClient
from src.api.main import app

# Verifies a new task is saved in DynamoDB with an initial PENDING status
def test_create_task_success(task_repository):
    created = task_repository.create_task("task-123", {"action": "process"})
    assert created is True

    item = task_repository.get_task("task-123")
    assert item is not None
    assert item["status"] == "PENDING"
    assert item["payload"] == {"action": "process"}

# Verifies conditional write blocks duplicate task_ids to enforce idempotency
def test_create_task_duplicate_idempotency(task_repository):
    first_attempt = task_repository.create_task("task-123", {"data": "first"})
    second_attempt = task_repository.create_task("task-123", {"data": "second"})

    assert first_attempt is True
    assert second_attempt is False

# Verifies TaskQueueProducer serializes and pushes a task message into SQS
def test_send_task_to_sqs_success(sqs_queue) -> None:
    producer = TaskQueueProducer(queue_url=sqs_queue["url"])
    msg_id = producer.send_task("task-456", {"metric": "latency"})
    assert isinstance(msg_id, str) and len(msg_id) > 0

    res = sqs_queue["client"].receive_message(QueueUrl = sqs_queue["url"], MaxNumberOfMessages = 1)
    assert "Messages" in res
    body = json.loads(res["Messages"][0]["Body"])
    assert body["task_id"] == "task-456"
    assert body["payload"]["metric"] == "latency"

# Verifies POST /tasks returns 202 Accepted and persists the task in DynamoDB
def test_submit_task_endpoint_success(task_repository, sqs_queue, monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", sqs_queue["url"])

    client = TestClient(app)
    response = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert response.status_code == 202
    assert response.json()["status"] == "PENDING"
    assert response.json() == {"task_id": "task-456", "status": "PENDING", "message": "Task accepted"}
    assert task_repository.get_task("task-456") is not None

# Verifies POST /tasks returns 409 Conflict when submitting an existing task_id
def test_submit_task_endpoint_duplicate(task_repository, sqs_queue, monkeypatch):
    monkeypatch.setenv("SQS_QUEUE_URL", sqs_queue["url"])

    client = TestClient(app)
    status = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert status.status_code == 202
    status2 = client.post("/tasks", json={"task_id": "task-456", "payload": {"metric": "latency"}})

    assert status2.status_code == 409
    assert status2.json()["detail"] == "Task ID already exists"

# Verifies GET /tasks/{task_id} returns 200 OK and the task state when the task exists
def test_get_task_status_found(task_repository):
    task_repository.create_task("task-100", {"action": "resize"})
    client = TestClient(app)
    response = client.get("/tasks/task-100")
    assert response.status_code == 200
    assert response.json()["task_id"] == "task-100"
    assert response.json()["status"] == "PENDING"


# Verifies GET /tasks/{task_id} returns 404 Not Found when querying a nonexistent task_id
def test_get_task_status_not_found(task_repository):
    client = TestClient(app)
    response = client.get("/tasks/missing-id")
    assert response.status_code == 404