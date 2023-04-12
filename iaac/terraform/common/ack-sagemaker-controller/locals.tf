locals {
  service = "sagemaker"

  name = "ack-${local.service}-controller"

  namespace = "ack-system"

  default_helm_config = {
    name        = local.name
    chart       = "${local.service}-chart"
    repository  = "oci://public.ecr.aws/aws-controllers-k8s"
    version     = "v1.2.1"
    namespace   = local.namespace
    description = "SageMaker Operator for Kubernetes (ACK)"
    values      = []
    timeout     = "240"
  }

  helm_config = merge(
    local.default_helm_config,
    var.helm_config
  )
}
