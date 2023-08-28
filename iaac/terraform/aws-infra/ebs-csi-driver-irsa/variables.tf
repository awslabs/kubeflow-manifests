variable "cluster_name" {
  type = string
}
variable "cluster_region" {
  type = string
}
variable "eks_oidc_provider_arn" {
  type = string
}
variable "tags" {
  type = any
}