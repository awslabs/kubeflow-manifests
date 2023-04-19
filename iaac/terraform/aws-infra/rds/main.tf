resource "aws_security_group" "public_access" {
  count = var.publicly_accessible ? 1 : 0

  name        = "rds-public-access"
  description = "Allow external access to MySQL on RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port        = 3306
    to_port          = 3306
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = var.tags
}

resource "aws_db_subnet_group" "rds_db_subnet_group" {
  subnet_ids = var.subnet_ids
  tags       = var.tags
}

resource "random_uuid" "db_snapshot_suffix" {
  keepers = {
    instance_class       = var.db_class
    db_name              = var.db_name
    username             = var.db_username
    password             = var.db_password
    multi_az             = var.multi_az
    db_subnet_group_name = aws_db_subnet_group.rds_db_subnet_group.id
    security_group_id    = var.security_group_id
  }
}

resource "aws_db_instance" "kubeflow_db" {
  allocated_storage         = var.db_allocated_storage
  engine                    = "mysql"
  engine_version            = var.mysql_engine_version
  instance_class            = var.db_class
  db_name                   = var.db_name
  username                  = var.db_username
  password                  = var.db_password
  multi_az                  = var.multi_az
  db_subnet_group_name      = aws_db_subnet_group.rds_db_subnet_group.id
  vpc_security_group_ids    = var.publicly_accessible ? [aws_security_group.public_access[0].id, var.security_group_id] : [var.security_group_id]
  backup_retention_period   = var.backup_retention_period
  storage_type              = var.storage_type
  deletion_protection       = var.deletion_protection
  max_allocated_storage     = var.max_allocated_storage
  publicly_accessible       = var.publicly_accessible
  final_snapshot_identifier = "snp-${random_uuid.db_snapshot_suffix.result}"
  tags                      = var.tags
}

resource "aws_secretsmanager_secret" "rds_secret" {
  name_prefix             = "rds-secret-"
  recovery_window_in_days = var.secret_recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "rds_secret_version" {
  secret_id = aws_secretsmanager_secret.rds_secret.id
  secret_string = jsonencode({
    username = aws_db_instance.kubeflow_db.username
    password = aws_db_instance.kubeflow_db.password
    database = aws_db_instance.kubeflow_db.db_name
    host     = aws_db_instance.kubeflow_db.address
    port     = tostring(aws_db_instance.kubeflow_db.port)
  })
}