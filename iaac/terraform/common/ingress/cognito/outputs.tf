output "kubelow_platform_domain" {
  value = "kubeflow.${data.aws_route53_zone.platform.name}"
}