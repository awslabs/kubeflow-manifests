output "iam_role_arn" {
  description = "ARN of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_arn
}

output "iam_role_name" {
  description = "Name of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_name
}