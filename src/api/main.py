from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from src.core.dynamodb import TaskStateRepository
from src.core.queue import TaskQueueProducer


class TaskRequest(BaseModel):
    task_id: str
    payload: dict

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

app = FastAPI()

@app.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
def submit_task(request: TaskRequest):
    repo = TaskStateRepository()
    producer = TaskQueueProducer()

    success = repo.create_task(request.task_id, request.payload)
    if not success:
        raise HTTPException(status_code=409, detail="Task ID already exists")

    producer.send_task(request.task_id, request.payload)

    return TaskResponse(task_id=request.task_id, status="PENDING", message="Task accepted")

@app.get("/health")
def root() -> dict:
    return {"status": "healthy"}