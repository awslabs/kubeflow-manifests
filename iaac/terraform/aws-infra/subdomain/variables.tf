variable "aws_route53_root_zone_name" {
  description = "TOP LEVEL/ROOT Route 53 hosted zone name (e.g. example.com). Must match exactly one zone."
  type        = string
}

variable "aws_route53_subdomain_zone_name" {
  description = "SUBDOMAIN Route 53 hosted zone name(e.g. platform.example.com) which will be created for Kubeflow Platform"
  type        = string
}

variable "tags" {
  description = "Additional tags (e.g. `map('BusinessUnit`,`XYZ`)"
  type        = map(string)
  default     = {}
}