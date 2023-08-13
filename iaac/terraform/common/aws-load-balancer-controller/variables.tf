# Required vars
variable "cluster_name" {
    type = string
}

variable "oidc_provider_arn" {
    type = string
}

# Optional vars

variable "chart_version" {
    type = string
    default = "1.5.5"
}

variable "chart_repo" {
    type = string
    default = "https://aws.github.io/eks-charts"
}

variable "role_name" {
    type = string
    default = "alb-controller"
}

variable "role_name_use_prefix" {
    type = bool
    default = true
}

variable "tags" {
    type = any
    default = {}
}