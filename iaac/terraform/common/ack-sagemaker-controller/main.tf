resource "aws_iam_policy" "sagemaker_ack_controller_studio_access" {
  name_prefix = "${local.service}-ack-controller-policy"
  description = "IAM policy for the ${local.service} ack controller"
  policy      = file("../../../awsconfigs/infra_configs/iam_ack_oidc_sm_studio_policy.json")
}

module "irsa" {
  source                            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/irsa?ref=v4.31.0"
  kubernetes_namespace              = local.namespace
  create_kubernetes_namespace       = true
  create_kubernetes_service_account = false
  kubernetes_service_account        = local.name
  irsa_iam_role_name                = format("%s-%s-%s-%s", "ack-sagemaker-controller", "irsa", var.addon_context.eks_cluster_id, var.addon_context.aws_region_name)
  irsa_iam_policies                 = ["arn:aws:iam::aws:policy/AmazonSageMakerFullAccess", aws_iam_policy.sagemaker_ack_controller_studio_access.arn]
  irsa_iam_role_path                = var.addon_context.irsa_iam_role_path
  irsa_iam_permissions_boundary     = var.addon_context.irsa_iam_permissions_boundary
  eks_cluster_id                    = var.addon_context.eks_cluster_id
  eks_oidc_provider_arn             = var.addon_context.eks_oidc_provider_arn
}

module "helm_addon" {
  source            = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons/helm-addon?ref=v4.31.0"
  manage_via_gitops = false
  helm_config       = local.helm_config
  set_values = [
    {
      name  = "aws.region"
      value = var.addon_context.aws_region_name
    },
    {
      name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
      value = module.irsa.irsa_iam_role_arn
    },
    {
      name  = "role.labels.rbac\\.authorization\\.kubeflow\\.org/aggregate-to-kubeflow-edit"
      value = "true"
    },
  ]

  addon_context = var.addon_context

  depends_on = [module.irsa]
}
