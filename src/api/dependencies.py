from src.core.dynamodb import TaskStateRepository
from src.core.queue import TaskQueueProducer


# Provides a TaskStateRepository instance for FastAPI dependency injection
def get_task_repository() -> TaskStateRepository:
    return TaskStateRepository()


# Provides a TaskQueueProducer instance for FastAPI dependency injection
def get_queue_producer() -> TaskQueueProducer:
    return TaskQueueProducer()