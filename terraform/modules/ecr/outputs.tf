# Outputs for ECR module

output "app_repository_url" {
  description = "URL of the app ECR repository"
  value       = aws_ecr_repository.app.repository_url
}

output "nginx_repository_url" {
  description = "URL of the nginx ECR repository"
  value       = aws_ecr_repository.nginx.repository_url
}

output "app_repository_name" {
  description = "Name of the app ECR repository"
  value       = aws_ecr_repository.app.name
}

output "nginx_repository_name" {
  description = "Name of the nginx ECR repository"
  value       = aws_ecr_repository.nginx.name
}