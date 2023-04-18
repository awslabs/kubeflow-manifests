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

variable "secret_recovery_window_in_days" {
  type    = number
  default = 7
}

variable "tags" {
  description = "Additional tags (e.g. `map('BusinessUnit`,`XYZ`)"
  type        = map(string)
  default     = {}
}