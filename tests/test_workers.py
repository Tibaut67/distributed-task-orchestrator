import json
from src.workers.processor import process_tasks, WorkerDaemon


# Verifies worker processes a valid task, marks it COMPLETED in DynamoDB, and deletes it from SQS
def test_process_tasks_success(task_repository, sqs_queue):
    #Arrange: seed DB and queue
    task_id = "task-1"
    payload = {"action": "resize"}
    task_repository.create_task(task_id, payload)
    sqs_queue["client"].send_message(
        QueueUrl=sqs_queue["url"],
        MessageBody=json.dumps({"task_id": task_id, "payload": payload})
    )

    #Act: run the worker
    processed = process_tasks(task_repository, sqs_queue["client"], sqs_queue["url"])

    #Assert: verify DB updated and queue is empty
    assert processed == 1
    assert task_repository.get_task(task_id)["status"] == "COMPLETED"
    assert "Messages" not in sqs_queue["client"].receive_message(QueueUrl=sqs_queue["url"])

# Verifies worker catches business logic errors, marks the task FAILED in DynamoDB, and deletes it from SQS
def test_process_tasks_failure(task_repository, sqs_queue):
    task_id = "task-1"
    payload = {"force_fail": True}
    task_repository.create_task(task_id, payload)
    sqs_queue["client"].send_message(
        QueueUrl=sqs_queue["url"],
        MessageBody=json.dumps({"task_id": task_id, "payload": payload})
    )

    processed = process_tasks(task_repository, sqs_queue["client"], sqs_queue["url"])

    assert processed == 1
    assert task_repository.get_task(task_id)["status"] == "FAILED"
    assert "Messages" not in sqs_queue["client"].receive_message(QueueUrl=sqs_queue["url"])

# Verifies worker catches malformed JSON poison pills and deletes them from SQS without crashing
def test_process_tasks_corrupted_json(task_repository, sqs_queue):
    sqs_queue["client"].send_message(
        QueueUrl=sqs_queue["url"],
        MessageBody="not-valid-json"
    )

    processed = process_tasks(task_repository, sqs_queue["client"], sqs_queue["url"])

    assert processed == 1
    assert "Messages" not in sqs_queue["client"].receive_message(QueueUrl=sqs_queue["url"])

# Verifies WorkerDaemon processes a task and exits cleanly when a shutdown signal is triggered
def test_worker_daemon_graceful_shutdown(task_repository, sqs_queue):
    task_id = "task-daemon-1"
    payload = {"action": "compile"}
    task_repository.create_task(task_id, payload)
    sqs_queue["client"].send_message(
        QueueUrl=sqs_queue["url"],
        MessageBody=json.dumps({"task_id": task_id, "payload": payload})
    )

    daemon = WorkerDaemon(task_repository, sqs_queue["client"], sqs_queue["url"], wait_time=0)
    daemon.stop(None, None)
    process_tasks(daemon.repo, daemon.sqs, daemon.queue_url, daemon.wait_time)

    assert daemon.running is False
    assert task_repository.get_task(task_id)["status"] == "COMPLETED"