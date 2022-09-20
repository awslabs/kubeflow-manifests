module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.9.0"
  manage_via_gitops = false
  helm_config = local.helm_config

  addon_context     = var.addon_context
}
