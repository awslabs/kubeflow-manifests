module "aws_load_balancer_controller" {
  source  = "aws-ia/eks-blueprints-addon/aws"
  version = "1.1.0"

  # https://github.com/aws/eks-charts/blob/master/stable/aws-load-balancer-controller/Chart.yaml
  name        = "aws-load-balancer-controller"
  description = "A Helm chart to deploy aws-load-balancer-controller for ingress resources"
  namespace   = "kube-system"
  # namespace creation is false here as kube-system already exists by default
  create_namespace = false
  chart            = "aws-load-balancer-controller"
  chart_version    = try(var.chart_version, "1.5.5") 
  repository       = try(var.chart_repo, "https://aws.github.io/eks-charts")  

  set = [
    {
      name  = "serviceAccount.name"
      value = "aws-load-balancer-controller-sa"
      }, {
      name  = "clusterName"
      value = var.cluster_name
    }]

  # IAM role for service account (IRSA)
  create_role                   = true
  set_irsa_names                = ["serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"]
  role_name                     = try(var.role_name, "alb-controller")
  role_name_use_prefix          = try(var.role_name_use_prefix, true)

  source_policy_documents       = [file("../../../awsconfigs/infra_configs/iam_alb_ingress_policy.json")]
  policy_description            = "IAM Policy for AWS Load Balancer Controller"

  oidc_providers = {
    this = {
      provider_arn = var.oidc_provider_arn
      service_account = "aws-load-balancer-controller-sa"
    }
  }

  tags = var.tags
}