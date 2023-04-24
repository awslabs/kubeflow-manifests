locals {
  name = "secrets-manager"

  default_helm_config = {
    name      = local.name
    namespace = "default" # change to namespace resources are being created in
    values    = []
    timeout   = "600"
  }

  helm_config = merge(
    local.default_helm_config,
    var.helm_config
  )

}
