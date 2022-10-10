output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.platform.arn
}

output "app_client_id" {
  description = "Cognito App client Id"
  value       = aws_cognito_user_pool_client.platform.id
}

output "user_pool_domain" {
  description = "Cognito User Pool Domain"
  value       = aws_cognito_user_pool_domain.platform.domain
}

output "logout_url" {
  description = "Logout URL"
  value       = "https://${aws_cognito_user_pool_domain.platform.domain}/logout?client_id=${aws_cognito_user_pool_client.platform.id}&logout_uri=https://kubeflow.${data.aws_route53_zone.platform.name}"
}