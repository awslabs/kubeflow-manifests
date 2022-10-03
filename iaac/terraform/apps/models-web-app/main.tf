module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.12.0"
  helm_config       = local.helm_config
  addon_context     = var.addon_context
}

# Wait 30 seconds after helm chart deployment
resource "time_sleep" "wait_30_seconds" {
  depends_on = [module.helm_addon]

  create_duration = "30s"
}
resource "null_resource" "next" {
  depends_on = [time_sleep.wait_30_seconds]
}