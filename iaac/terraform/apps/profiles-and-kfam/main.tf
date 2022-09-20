resource "aws_iam_policy" "profile_controller_policy" {
  name_prefix        = "profile-controller-policy"
  description = "IAM policy for the kubeflow pipelines profile controller"
  policy        = "${file("../../../awsconfigs/infra_configs/iam_profile_controller_policy.json")}"
}

module "irsa" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/irsa?ref=v4.9.0"
  kubernetes_namespace = "kubeflow"
  create_kubernetes_namespace = false
  create_kubernetes_service_account = false
  kubernetes_service_account = "profiles-controller-service-account"
  irsa_iam_role_name = format("%s-%s-%s-%s", "profiles-controller", "irsa", var.addon_context.eks_cluster_id, var.addon_context.aws_region_name)
  irsa_iam_policies = [aws_iam_policy.profile_controller_policy.arn]
  irsa_iam_role_path                = var.addon_context.irsa_iam_role_path
  irsa_iam_permissions_boundary     = var.addon_context.irsa_iam_permissions_boundary
  eks_cluster_id                    = var.addon_context.eks_cluster_id
  eks_oidc_provider_arn             = var.addon_context.eks_oidc_provider_arn
}

resource "kubernetes_service_account_v1" "profile_controller_sa" {
  metadata {
    name        = module.irsa.service_account
    namespace   = module.irsa.namespace
    annotations = { 
      "eks.amazonaws.com/role-arn" : module.irsa.irsa_iam_role_arn, 
      "meta.helm.sh/release-name": local.name,
      "meta.helm.sh/release-namespace": "default"
    }
    labels = {
      "app.kubernetes.io/managed-by": "Helm"
    }
  }

  automount_service_account_token = true
}

module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.9.0"
  helm_config       = local.helm_config
  addon_context     = var.addon_context

  depends_on = [kubernetes_service_account_v1.profile_controller_sa]
}
