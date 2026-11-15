from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from src.core.dynamodb import TaskStateRepository
from src.core.queue import TaskQueueProducer

# Validates incoming task creation request body
class TaskRequest(BaseModel):
    task_id: str
    payload: dict

# Formats the standard response returned when a task is accepted
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

app = FastAPI()

# Creates an idempotent task record in DynamoDB and enqueues it to SQS (returns 409 on duplicate)
@app.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
def submit_task(request: TaskRequest):
    repo = TaskStateRepository()
    producer = TaskQueueProducer()

    success = repo.create_task(request.task_id, request.payload)
    if not success:
        raise HTTPException(status_code=409, detail="Task ID already exists")

    producer.send_task(request.task_id, request.payload)

    return TaskResponse(task_id=request.task_id, status="PENDING", message="Task accepted")

# Returns API health status for container and load balancer checks
@app.get("/health")
def root() -> dict:
    return {"status": "healthy"}

# Queries DynamoDB by task_id and returns the task state (200 OK) or 404 Not Found if missing
@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    repo = TaskStateRepository()
    task = repo.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task