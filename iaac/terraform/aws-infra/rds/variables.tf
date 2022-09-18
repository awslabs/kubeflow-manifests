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

variable "multi_az" {
  type        = string
  description = "Enables multi AZ for the master database"
  default     = "true"
}

variable "secret_recovery_window_in_days" {
  type = number
  default = 7
}
