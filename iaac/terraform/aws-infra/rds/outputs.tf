output "rds_secret_name" {
  value = aws_secretsmanager_secret.rds_secret.name
}

output "rds_endpoint" {
  value = aws_db_instance.kubeflow_db.address
}