resource "aws_db_subnet_group" "rds_db_subnet_group" {
  subnet_ids = var.subnet_ids
}

resource "random_uuid" "db_snapshot_suffix" {
  keepers = {
    instance_class       = var.db_class
    db_name              = var.db_name
    username = var.db_username
    password = var.db_password
    multi_az = var.multi_az
    db_subnet_group_name = aws_db_subnet_group.rds_db_subnet_group.id
    security_group_id = var.security_group_id
  }
}

resource "aws_db_instance" "kubeflow_db" {
  allocated_storage    = var.db_allocated_storage
  engine               = "mysql"
  engine_version       = var.mysql_engine_version
  instance_class       = var.db_class
  db_name                 = var.db_name
  username = var.db_username
  password = var.db_password
  multi_az = var.multi_az
  db_subnet_group_name = aws_db_subnet_group.rds_db_subnet_group.id
  vpc_security_group_ids = [var.security_group_id]
  final_snapshot_identifier = "snp-${random_uuid.db_snapshot_suffix.result}"
}

resource "aws_secretsmanager_secret" "rds_secret" {
  name_prefix = "rds-secret-"
  recovery_window_in_days = var.secret_recovery_window_in_days
}

resource "aws_secretsmanager_secret_version" "rds_secret_version" {
  secret_id     = aws_secretsmanager_secret.rds_secret.id
  secret_string = jsonencode({
    username = aws_db_instance.kubeflow_db.username
    password = aws_db_instance.kubeflow_db.password
    database = aws_db_instance.kubeflow_db.db_name
    host = aws_db_instance.kubeflow_db.address
    port = tostring(aws_db_instance.kubeflow_db.port)
  })
}