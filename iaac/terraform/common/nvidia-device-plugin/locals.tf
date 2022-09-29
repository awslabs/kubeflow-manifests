# todo: replace with https://github.com/aws-ia/terraform-aws-eks-blueprints/pull/995 when it is present in the latest release

locals {
  name = "nvidia-device-plugin"
  namespace = "kube-system"

  default_helm_config = {
    name        = local.name
    chart       = local.name
    repository  = "https://nvidia.github.io/k8s-device-plugin"
    version     = "0.12.3"
    namespace   = local.namespace
    description = "Installs the NVIDIA device plugin for Kubernetes"
    values      = []
    timeout     = "600"
  }

  helm_config = merge(
    local.default_helm_config,
    var.helm_config
  )
}
