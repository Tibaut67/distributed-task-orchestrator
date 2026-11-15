# Provisions the on-demand DynamoDB table for tracking task state and idempotency
resource "aws_dynamodb_table" "task_state_table" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "task_id"

  attribute {
    name = "task_id"
    type = "S"
  }
}