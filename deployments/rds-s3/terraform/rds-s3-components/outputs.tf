output "rds_endpoint" {
  value       = try(module.rds[0].rds_endpoint, null)
  description = "The address of the RDS endpoint"
}

output "s3_bucket_name" {
  value       = try(module.s3[0].s3_bucket_name, null)
  description = "The name of the created S3 bucket"
}

output "irsa_kubeflow_pipeline_role_name" {
  value       = try(module.kubeflow_pipeline_irsa[0].irsa_iam_role_name, null)
  description = " The irsa role name for KFP"
}

output "irsa_user_namespace_role_name" {
  value       = try(module.user_namespace_irsa[0].irsa_iam_role_name, null)
  description = " The irsa role name for kubeflow-user-example-com"
}