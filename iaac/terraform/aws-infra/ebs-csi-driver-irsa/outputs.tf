output "iam_role_arn" {
  description = "ARN of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_arn
}

output "iam_role_name" {
  description = "Name of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_name
}

output "iam_role_path" {
  description = "Path of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_path
}

output "iam_role_unique_id" {
  description = "Unique ID of IAM role"
  value       = module.ebs_csi_driver_irsa.iam_role_unique_id
}