locals {
  name = "nvidia-device-plugin"
  namespace = "nvidia-device-plugin"

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
