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