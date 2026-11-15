# Provisions an HTTP API Gateway to route public traffic to the FastAPI Lambda
resource "aws_apigatewayv2_api" "http_api" {
  name          = "task-orchestrator-http-api"
  protocol_type = "HTTP"
}

# Connects API Gateway requests to the FastAPI Lambda function via proxy integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.api_lambda.invoke_arn
  payload_format_version = "2.0"
}

# Routes all incoming HTTP paths to the FastAPI integration
resource "aws_apigatewayv2_route" "default_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}