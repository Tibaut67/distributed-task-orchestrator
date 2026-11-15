
# Base exception class for all custom errors in the task orchestrator
class TaskOrchestratorError(Exception):
    pass

# Raised when a background worker encounters a permanent business logic failure while processing a task
class TaskExecutionError(TaskOrchestratorError):
    pass