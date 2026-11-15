# Distributed Task Orchestrator

An asynchronous, fault-tolerant task ingestion and background processing system built with **Python**, **FastAPI**, **AWS SQS**, **AWS DynamoDB**, **Docker**, and **Terraform**.

## Architecture & Engineering Highlights

1. **Idempotent Task Ingestion (`POST /tasks`)**: Uses DynamoDB conditional writes (`attribute_not_exists(task_id)`) to guarantee at-most-once task creation under network retries, returning `202 Accepted` on creation or `409 Conflict` on duplicate submissions.
2. **Decoupled Producer-Consumer Pipeline**: FastAPI offloads task payloads to AWS SQS for asynchronous execution, maintaining low ingestion latency under load.
3. **Fault-Tolerant Worker Daemon**:
   - **SQS Long Polling (`WaitTimeSeconds=20`)**: Eliminates empty-queue polling overhead and reduces AWS API costs.
   - **Poison-Pill Isolation vs. Transient Retries**: Permanently malformed messages (`JSONDecodeError`, `KeyError`, `TaskExecutionError`) are marked `FAILED` in DynamoDB and purged from SQS, while transient AWS `ClientError` exceptions leave messages in-flight to retry automatically after the SQS visibility timeout.
   - **Graceful Shutdown (`SIGINT` / `SIGTERM`)**: Intercepts OS termination signals to finish in-flight message batches before shutting down the container.

## Performance Benchmarks (200-Task Batch)
- **Ingestion Latency**: `13.19 ms` (P50) | `16.93 ms` (P95) | `68.58 ms` (P99)
- **Ingestion Throughput**: `67.6 req/sec` (single-threaded synchronous client)
- **Worker Batch Throughput**: `107.4 tasks/sec`

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Pydantic, Uvicorn
- **Cloud & IaC**: AWS SQS, AWS DynamoDB, Boto3, Terraform
- **Containerization & Testing**: Docker, Docker Compose, LocalStack, Pytest, Moto

## Running Tests & Benchmarks Locally

```bash
# Run the full integration test suite (11 tests)
.venv/Scripts/pytest

# Run the ingestion & worker throughput benchmark
.venv/Scripts/python -m benchmarks.benchmark_runner
