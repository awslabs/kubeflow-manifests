variable "aws_route53_subdomain_zone_name" {
  description = "SUBDOMAIN Route 53 hosted zone name(e.g. platform.example.com) which will be used for Kubeflow Platform. Must match exactly one zone"
  type        = string
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN"
  type        = string
}

variable "cognito_app_client_id" {
  description = "Cognito App client Id"
  type        = string
}

variable "cognito_user_pool_domain" {
  description = "Cognito User Pool Domain"
  type        = string
}

variable "load_balancer_scheme" {
  description = "Load Balancer Scheme"
  type        = string
  default     = "internet-facing"
}

variable "tags" {
  description = "Additional tags (e.g. `map('BusinessUnit`,`XYZ`)"
  type        = map(string)
  default     = {}
}