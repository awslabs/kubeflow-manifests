locals {
  name = "rds-s3-kubeflow"
  cluster_name = coalesce(var.cluster_name, local.name)
  region       = var.cluster_region
  eks_version = var.eks_version

  vpc_cidr = "10.0.0.0/16"
  az_count = local.region == "us-west-1" ? 2 : 3
  azs      = slice(data.aws_availability_zones.available.names, 0, local.az_count)

  tags = {
    Blueprint  = local.name
    GithubRepo = "github.com/awslabs/kubeflow-manifests"
    Platform = "kubeflow-on-aws"
    KubeflowVersion = "1.6"
  }

  kf_helm_repo_path = var.kf_helm_repo_path
}

provider "aws" {
  region = local.region
}

provider "kubernetes" {
  host                   = module.eks_blueprints.eks_cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks_blueprints.eks_cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    # This requires the awscli to be installed locally where Terraform is executed
    args = ["eks", "get-token", "--cluster-name", module.eks_blueprints.eks_cluster_id]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks_blueprints.eks_cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks_blueprints.eks_cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", module.eks_blueprints.eks_cluster_id]
    }
  }
}

data "aws_availability_zones" "available" {}

#---------------------------------------------------------------
# EKS Blueprints
#---------------------------------------------------------------
module "eks_blueprints" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints?ref=v4.9.0"

  cluster_name    = local.cluster_name
  cluster_version = local.eks_version

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnets

  managed_node_groups = {
    mg_5 = {
      node_group_name = "managed-ondemand"
      instance_types  = ["m5.large"]
      min_size        = 5
      desired_size    = 5
      max_size        = 10
      subnet_ids      = module.vpc.private_subnets
    }
  }

  tags = local.tags
}

module "eks_blueprints_kubernetes_addons" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons?ref=v4.9.0"

  eks_cluster_id       = module.eks_blueprints.eks_cluster_id
  eks_cluster_endpoint = module.eks_blueprints.eks_cluster_endpoint
  eks_oidc_provider    = module.eks_blueprints.oidc_provider
  eks_cluster_version  = module.eks_blueprints.eks_cluster_version

  # EKS Managed Add-ons
  enable_amazon_eks_vpc_cni    = true
  enable_amazon_eks_coredns    = true
  enable_amazon_eks_kube_proxy = true
  enable_amazon_eks_aws_ebs_csi_driver = true

  # EKS Blueprints Add-ons
  enable_cert_manager = true
  enable_aws_load_balancer_controller = true
  enable_aws_efs_csi_driver = true
  enable_aws_fsx_csi_driver = true

  secrets_store_csi_driver_helm_config = {
    namespace   = "kube-system"
    set = [
      {
        name = "syncSecret.enabled",
        value = "true"
      },
      {
        name = "enableSecretRotation",
        value = "true"
      }
    ]
  }
  enable_secrets_store_csi_driver = true


  csi_secrets_store_provider_aws_helm_config = {
    namespace = "kube-system"
    set = [
      {
        name = "secrets-store-csi-driver.install",
        value = "false"
      }
    ]
  }
  enable_secrets_store_csi_driver_provider_aws = true

  tags = local.tags

}

# todo: update the blueprints repo code to export the desired values as outputs
module "eks_blueprints_outputs" {
  source = "../../../iaac/terraform/utils/blueprints-extended-outputs"

  eks_cluster_id       = module.eks_blueprints.eks_cluster_id
  eks_cluster_endpoint = module.eks_blueprints.eks_cluster_endpoint
  eks_oidc_provider    = module.eks_blueprints.oidc_provider
  eks_cluster_version  = module.eks_blueprints.eks_cluster_version

  tags = local.tags
}

module "kubeflow_components" {
  source = "./rds-s3-components"

  kf_helm_repo_path = local.kf_helm_repo_path
  addon_context = module.eks_blueprints_outputs.addon_context
  enable_aws_telemetry = var.enable_aws_telemetry

  use_rds = var.use_rds
  use_s3 = var.use_s3

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  security_group_id = module.eks_blueprints.cluster_primary_security_group_id
  db_name = var.db_name
  db_username = var.db_username
  db_password = var.db_password
  db_class = var.db_class
  db_allocated_storage = var.db_allocated_storage
  multi_az = var.multi_az
  secret_recovery_window_in_days = var.secret_recovery_window_in_days
  generate_db_password = var.generate_db_password

  force_destroy_s3_bucket = var.force_destroy_s3_bucket
  aws_access_key = var.aws_access_key
  aws_secret_key = var.aws_secret_key
}

#---------------------------------------------------------------
# Supporting Resources
#---------------------------------------------------------------
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "3.14.4"

  name = local.name
  cidr = local.vpc_cidr

  azs             = local.azs
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 3, k)]
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 3, k + length(local.azs))]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  # Manage so we can name
  manage_default_network_acl    = true
  default_network_acl_tags      = { Name = "${local.name}-default" }
  manage_default_route_table    = true
  default_route_table_tags      = { Name = "${local.name}-default" }
  manage_default_security_group = true
  default_security_group_tags   = { Name = "${local.name}-default" }

  public_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                      = 1
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"             = 1
  }

  tags = local.tags
}
