# tflint-ignore: terraform_unused_declarations
variable "cluster_name" {
  description = "Name of cluster"
  type        = string
  default = "tf-cognito-cluster" #todo remove
}

variable "cluster_region" {
  description = "Region to create the cluster"
  type        = string
  default = "us-west-2" #todo remove
}

variable "eks_version" {
  description = "The EKS version to use"
  type        = string
  default     = "1.22"
}

variable "cognito_user_pool_name" {
  description = "Cognito User Pool name"
  type        = string
  default = "tf-cognito-up" #todo remove
}

variable "aws_route53_subdomain_zone_name" {
  description = "SUBDOMAIN Route 53 hosted zone name(e.g. platform.example.com) which will be used for Kubeflow Platform. Must match exactly one zone"
  type        = string
  default = "tmp.rkharse.people.aws.dev" #todo remove
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