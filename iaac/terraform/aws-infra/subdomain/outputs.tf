output "aws_route53_subdomain_zone_name" {
  description = "Subdomain which will be used for Kubeflow Platform (e.g. platform.example.com)"
  value       = aws_route53_zone.platform.name
}