module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.9.0"
  helm_config       = local.helm_config
  addon_context     = var.addon_context
}

# todo: replace w deterministic
# Wait 60 seconds after helm chart deployment
resource "time_sleep" "wait_60_seconds" {
  depends_on = [module.helm_addon]

  create_duration = "60s"
}
resource "null_resource" "next" {
  depends_on = [time_sleep.wait_60_seconds]
}
