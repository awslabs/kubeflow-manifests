# tflint-ignore: terraform_unused_declarations
variable "cluster_name" {
  description = "Name of cluster"
  type        = string
}

variable "cluster_region" {
  description = "Region to create the cluster"
  type        = string
}

variable "eks_version" {
  description = "The EKS version to use"
  type        = string
  default     = "1.22"
}

variable "node_instance_type" {
  description = "The instance type of an EKS node"
  type        = string
  default     = "m5.xlarge"
}

variable "install_nvidia_device_plugin" {
  description = "Installs the nvidia device plugin. Required for GPU training"
  type = bool
  default = false
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
  type = bool
  default = true
}

variable "load_balancer_scheme" {
  description = "Load Balancer Scheme"
  type        = string
  default = "internet-facing"
}

variable "enable_aws_telemetry" {
  description = "Enable AWS telemetry component"
  type = bool
  default = true
}

variable "kf_helm_repo_path" {
  description = "Full path to the location of the helm repo for KF"
  type        = string
  default = "../../.."
}