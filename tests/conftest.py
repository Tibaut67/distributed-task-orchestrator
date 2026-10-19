import os
import pytest
import boto3
from moto import mock_aws
from src.core.dynamodb import TaskStateRepository

@pytest.fixture(autouse=True)
def aws_credentials():
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "testing"


@pytest.fixture
def task_repository():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="TaskStateTable",
            KeySchema=[{"AttributeName": "task_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "task_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST")
        repo = TaskStateRepository("TaskStateTable")
        yield repo


@pytest.fixture
def sqs_queue():
    with mock_aws():
        client = boto3.client("sqs", region_name="us-east-1")
        res = client.create_queue(QueueName="task-processing-queue")
        yield {"url": res["QueueUrl"], "client": client}