# tflint-ignore: terraform_unused_declarations
variable "cluster_name" {
  description = "Name of cluster"
  type        = string

  validation {
    condition     = length(var.cluster_name) > 0 && length(var.cluster_name) <= 19
    error_message = "The cluster name must be between [1, 19] characters"
  }
}

variable "cluster_region" {
  description = "Region to create the cluster"
  type        = string
}

variable "eks_version" {
  description = "The EKS version to use"
  type        = string
  default     = "1.25"
}

variable "node_instance_type" {
  description = "The instance type of an EKS node"
  type        = string
  default     = "m5.xlarge"
}

variable "node_instance_type_gpu" {
  description = "The instance type of a gpu EKS node. Will result in the creation of a separate gpu node group when not null"
  type        = string
  default     = null
}

variable "enable_aws_telemetry" {
  description = "Enable AWS telemetry component"
  type        = bool
  default     = true
}

variable "kf_helm_repo_path" {
  description = "Full path to the location of the helm repo for KF"
  type        = string
  default     = "../../.."
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
