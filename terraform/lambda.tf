# Defines the IAM execution role for serverless Lambda functions
resource "aws_iam_role" "lambda_exec_role" {
  name = "task_orchestrator_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Provisions the FastAPI ingestion Lambda function (using Mangum adapter)
resource "aws_lambda_function" "api_lambda" {
  function_name = "task-orchestrator-api"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "src.api.main.handler"
  runtime       = "python3.12"
  filename      = "deployment.zip"

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.task_state_table.name
      SQS_QUEUE_URL       = aws_sqs_queue.task_queue.id
    }
  }
}