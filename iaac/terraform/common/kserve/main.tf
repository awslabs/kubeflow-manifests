module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.12.1"
  helm_config       = local.helm_config
  addon_context     = var.addon_context
}
