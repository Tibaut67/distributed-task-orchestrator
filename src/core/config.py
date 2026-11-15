import os


# Centralizes environment variable configuration and default AWS settings
class Settings:
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_NAME: str = os.getenv("DYNAMODB_TABLE_NAME", "TaskStateTable")
    SQS_QUEUE_URL: str = os.getenv("SQS_QUEUE_URL", "")


settings = Settings()