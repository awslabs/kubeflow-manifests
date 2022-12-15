module "helm_addon" {
<<<<<<< HEAD
  source        = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.18.1"
  helm_config   = local.helm_config
  addon_context = var.addon_context
=======
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.12.1"
  helm_config       = local.helm_config
  addon_context     = var.addon_context
>>>>>>> main
}
