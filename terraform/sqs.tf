# Provisions the Dead-Letter Queue (DLQ) to isolate repeatedly failed messages
resource "aws_sqs_queue" "task_dlq" {
  name = "${var.queue_name}-dlq"
}

# Provisions the primary SQS queue with long polling and a 3-attempt redrive policy
resource "aws_sqs_queue" "task_queue" {
  name                       = var.queue_name
  visibility_timeout_seconds = 30
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.task_dlq.arn
    maxReceiveCount     = 3
  })
}