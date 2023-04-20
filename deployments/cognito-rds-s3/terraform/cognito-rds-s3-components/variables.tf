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
  type        = bool
  default     = true
}

variable "use_rds" {
  type    = bool
  default = true
}

variable "use_s3" {
  type    = bool
  default = true
}

variable "pipeline_s3_credential_option" {
  description = "The credential type to use to authenticate KFP to use S3. One of [irsa, static]"
  type        = string
  default     = "irsa"

  validation {
    condition     = "irsa" == var.pipeline_s3_credential_option || "static" == var.pipeline_s3_credential_option
    error_message = "The pipeline_s3_credential_option must be one of [irsa, static]"
  }
}

variable "use_cognito" {
  type    = bool
  default = true
}

# RDS

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
  default     = "kubeflow"
}

variable "db_username" {
  type        = string
  description = "Database admin account username"
  default     = "admin"
}

variable "db_password" {
  type        = string
  description = "Database admin account password"
  default     = null
}

variable "db_class" {
  type        = string
  description = "Database instance type"
  default     = "db.m5.large"
}

variable "db_allocated_storage" {
  type        = string
  description = "The size of the database (Gb)"
  default     = "20"
}

variable "mysql_engine_version" {
  type        = string
  description = "The engine version of MySQL"
  default     = "8.0.32"
}

variable "backup_retention_period" {
  type        = number
  description = "Number of days to retain backups for"
  default     = 7
}

variable "storage_type" {
  type        = string
  description = "Instance storage type: standard, gp2, or io1"
  default     = "gp2"
}

variable "deletion_protection" {
  type        = bool
  description = "Prevents the deletion of the instance when set to true"
  default     = true
}

variable "max_allocated_storage" {
  type        = number
  description = "The upper limit of scalable storage (Gb)"
  default     = 1000
}

variable "publicly_accessible" {
  type        = bool
  description = "Makes the instance publicly accessible when true"
  default     = false
}

variable "multi_az" {
  type        = string
  description = "Enables multi AZ for the master database"
  default     = "true"
}

variable "mlmdb_name" {
  type        = string
  default     = "metadb"
  description = "Name of the mlm DB to create"
}

variable "generate_db_password" {
  description = "Generates a random admin password for the RDS database. Is overriden by db_password"
  type        = bool
  default     = false
}

# S3

variable "minio_service_region" {
  type        = string
  default     = null
  description = "S3 service region. Change this field if the S3 bucket will be in a different region than the EKS cluster"
}

variable "minio_service_host" {
  type        = string
  default     = "s3.amazonaws.com"
  description = "S3 service host DNS. This field will need to be changed when making requests from other partitions e.g. China Regions"
}

variable "secret_recovery_window_in_days" {
  type    = number
  default = 7
}

variable "force_destroy_s3_bucket" {
  type        = bool
  description = "Destroys s3 bucket even when the bucket is not empty"
  default     = false
}

variable "minio_aws_access_key_id" {
  type        = string
  description = "AWS access key ID to authenticate minio client"
}

variable "minio_aws_secret_access_key" {
  type        = string
  description = "AWS secret access key to authenticate minio client"
}

# Cognito

variable "cognito_user_pool_name" {
  description = "Cognito User Pool name"
  type        = string
}

variable "aws_route53_root_zone_name" {
  description = "TOP LEVEL/ROOT Route 53 hosted zone name (e.g. example.com). Must match exactly one zone."
  type        = string
}

variable "aws_route53_subdomain_zone_name" {
  description = "SUBDOMAIN Route 53 hosted zone name(e.g. platform.example.com) which will be used for Kubeflow Platform. Must match exactly one zone"
  type        = string
}

variable "create_subdomain" {
  description = "Creates a subdomain with the name provided in var.aws_route53_subdomain_zone_name"
  type        = bool
  default     = true
}

variable "load_balancer_scheme" {
  description = "Load Balancer Scheme"
  type        = string
  default     = "internet-facing"
}

variable "notebook_enable_culling" {
  description = "Enable Notebook culling feature. If set to true then the Notebook Controller will scale all Notebooks with Last activity older than the notebook_cull_idle_time to zero"
  type        = string
  default     = false
}

variable "notebook_cull_idle_time" {
  description = "If a Notebook's LAST_ACTIVITY_ANNOTATION from the current timestamp exceeds this value then the Notebook will be scaled to zero (culled). ENABLE_CULLING must be set to 'true' for this setting to take effect.(minutes)"
  type        = string
  default     = 30
}

variable "notebook_idleness_check_period" {
  description = "How frequently the controller should poll each Notebook to update its LAST_ACTIVITY_ANNOTATION (minutes)"
  type        = string
  default     = 5
}

variable "tags" {
  description = "Additional tags (e.g. `map('BusinessUnit`,`XYZ`)"
  type        = map(string)
  default     = {}
}