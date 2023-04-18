# todo add https only policy as a configurable option
# does this need to be a configurable option in helm also?

resource "aws_s3_bucket" "artifact_store" {
  bucket_prefix = "kf-artifact-store-"
  force_destroy = var.force_destroy_bucket
  tags          = var.tags
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifact_store_encryption" {
  bucket = aws_s3_bucket.artifact_store.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_secretsmanager_secret" "s3_secret" {
  name_prefix             = "s3-secret-"
  recovery_window_in_days = var.secret_recovery_window_in_days
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "s3_secret_version" {
  secret_id = aws_secretsmanager_secret.s3_secret.id
  secret_string = jsonencode({
    accesskey = var.minio_aws_access_key_id
    secretkey = var.minio_aws_secret_access_key
  })
}

resource "aws_s3_bucket_public_access_block" "artifact_store_block_access" {
  bucket = aws_s3_bucket.artifact_store.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}