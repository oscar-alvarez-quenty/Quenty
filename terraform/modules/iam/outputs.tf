# Outputs for IAM module

output "ecs_execution_role_arn" {
  description = "ARN of the ECS execution role"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_autoscaling_role_arn" {
  description = "ARN of the ECS autoscaling role"
  value       = aws_iam_role.ecs_autoscaling_role.arn
}

output "ecs_events_role_arn" {
  description = "ARN of the ECS events role"
  value       = aws_iam_role.ecs_events_role.arn
}