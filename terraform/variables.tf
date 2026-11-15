# Defines configurable input variables for the AWS deployment
variable "aws_region" {
  description = "Target AWS region for provisioning resources"
  type        = string
  default     = "us-east-1"
}

variable "table_name" {
  description = "DynamoDB table name for storing task state"
  type        = string
  default     = "TaskStateTable"
}

variable "queue_name" {
  description = "Primary SQS queue name for task ingestion"
  type        = string
  default     = "task-processing-queue"
}