locals {
  name = "kubeflow-pipelines"

  # add vars input here
  set_values_map = {
  }

  set_values = [for k,v in local.set_values_map : {name = k, value = v} if v != ""]

  default_helm_config = {
    name        = local.name
    version     = "0.1.0"
    namespace   = "default"    # change to namespace resources are being created it
    values      = []
    timeout     = "600"
  }
  
  helm_config = merge(
    local.default_helm_config,
    var.helm_config,
    {
      set = concat(local.set_values, try(var.helm_config["set"], []))
    }
  )

}
