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

variable "enable_aws_telemetry" {
  description = "Enable AWS telemetry component"
  type        = bool
  default     = true
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