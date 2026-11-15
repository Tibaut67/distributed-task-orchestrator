import time
import uuid
import json
import boto3
from moto import mock_aws
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.dynamodb import TaskStateRepository
from src.workers.processor import process_tasks


# Runs an end-to-end ingestion and worker throughput benchmark to generate benchmark metrics
def run_benchmark(num_tasks: int = 200):
    with mock_aws():
        # Setup mock DynamoDB and SQS
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="TaskStateTable",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue_url = sqs.create_queue(QueueName="task-processing-queue")["QueueUrl"]

        import os
        os.environ["SQS_QUEUE_URL"] = queue_url
        os.environ["DYNAMODB_TABLE_NAME"] = "TaskStateTable"

        client = TestClient(app)
        repo = TaskStateRepository("TaskStateTable")

        # 1. Measure API Ingestion Latency & Throughput
        latencies = []
        start_ingest = time.perf_counter()
        for _ in range(num_tasks):
            t0 = time.perf_counter()
            res = client.post("/tasks", json={"task_id": str(uuid.uuid4()), "payload": {"job": "bench"}})
            latencies.append((time.perf_counter() - t0) * 1000)
            assert res.status_code == 202
        total_ingest_time = time.perf_counter() - start_ingest

        # 2. Measure Worker Batch Processing Throughput
        processed_total = 0
        start_worker = time.perf_counter()
        while processed_total < num_tasks:
            processed_total += process_tasks(repo, sqs, queue_url, wait_time=0)
        total_worker_time = time.perf_counter() - start_worker

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        p99 = latencies[int(len(latencies) * 0.99)]

        print(f"--- Benchmark Results ({num_tasks} Tasks) ---")
        print(f"Ingestion Throughput : {num_tasks / total_ingest_time:.1f} req/sec")
        print(f"Ingestion Latency    : P50={p50:.2f}ms | P95={p95:.2f}ms | P99={p99:.2f}ms")
        print(f"Worker Throughput    : {processed_total / total_worker_time:.1f} tasks/sec")


if __name__ == "__main__":
    run_benchmark()