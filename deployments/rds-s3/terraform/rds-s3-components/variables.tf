variable "kf_helm_repo_path" {
  description = "Full path to the location of the helm folder to install from for KF 1.6"
  type        = string
}

variable "addon_context" {
  description = "Input configuration for the addon"
  type = object({
    aws_caller_identity_account_id = string
    aws_caller_identity_arn        = string
    aws_eks_cluster_endpoint       = string
    aws_partition_id               = string
    aws_region_name                = string
    eks_cluster_id                 = string
    eks_oidc_issuer_url            = string
    eks_oidc_provider_arn          = string
    tags                           = map(string)
    irsa_iam_role_path             = string
    irsa_iam_permissions_boundary  = string
  })
}

variable "enable_aws_telemetry" {
  description = "Enable AWS telemetry component"
  type = bool
  default = true
}

variable "use_rds" {
  type = bool
  default = true
}

variable "use_s3" {
  type = bool
  default = true
}

variable "vpc_id" {
  type        = string
  description = "VPC of the EKS cluster"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnet ids of the EKS cluster"
}

variable "security_group_id" {
  type        = string
  description = "SecurityGroup Id of a EKS Worker Node"
}

variable "db_name" {
  type        = string
  description = "Database name"
  default = "kubeflow"
}

variable "db_username" {
  type        = string
  description = "Database admin account username"
  default = "admin"
}

variable "db_password" {
  type        = string
  description = "Database admin account password"
  default = null
}

variable "db_class" {
  type        = string
  description = "Database instance type"
  default = "db.m5.large"
}

variable "db_allocated_storage" {
  type        = string
  description = "The size of the database (Gb)"
  default = "20"
}

variable "mysql_engine_version" {
  type        = string
  description = "The engine version of MySQL"
  default = "8.0.30"
}

variable "backup_retention_period" {
  type        = number
  description = "Number of days to retain backups for"
  default = 7
}

variable "storage_type" {
  type        = string
  description = "Instance storage type: standard, gp2, or io1"
  default = "gp2"
}

variable "deletion_protection" {
  type        = bool
  description = "Prevents the deletion of the instance when set to true"
  default = true
}

variable "max_allocated_storage" {
  type        = number
  description = "The upper limit of scalable storage (Gb)"
  default = 1000
}

variable "publicly_accessible" {
  type        = bool
  description = "Makes the instance publicly accessible when true"
  default = false
}

variable "multi_az" {
  type        = string
  description = "Enables multi AZ for the master database"
  default     = "true"
}

variable "mlmdb_name" {
  type        = string
  default = "metadb"
  description = "Name of the mlm DB to create"
}

variable "minio_service_region" {
  type        = string
  default = null
  description = "S3 service region. Change this field if the S3 bucket will be in a different region than the EKS cluster"
}

variable "minio_service_host" {
  type        = string
  default = "s3.amazonaws.com"
  description = "S3 service host DNS. This field will need to be changed when making requests from other partitions e.g. China Regions"
}

variable "secret_recovery_window_in_days" {
  type = number
  default = 7
}

variable "generate_db_password" {
  description = "Generates a random admin password for the RDS database. Is overriden by db_password"
  type = bool
  default = false
}

variable "force_destroy_s3_bucket" {
  type = bool
  description = "Destroys s3 bucket even when the bucket is not empty"
  default = false
}

variable "minio_aws_access_key_id" {
  type        = string
  description = "AWS access key ID to authenticate minio client"
}

variable "minio_aws_secret_access_key" {
  type        = string
  description = "AWS secret access key to authenticate minio client"
}
