+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with AWS Cognito as an identity provider using Terraform"
weight = 30
+++

> Note: Terraform deployment option is still in preview.

## Background

This guide will walk you through using Terraform to:
- Create a VPC
- Create an EKS cluster
- Create a Route53 subdomain
- Create a Cognito user pool
- Deploy Kubeflow with Cognito as an identity provider

Find additional information on [using Cognito with the AWS Distribution for Kubeflow]({{< ref "./manifest/guide/#background" >}}) in this guide. You can also check [Terraform documentation](https://www.terraform.io/docs).

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#install-necessary-tools" >}})

Additionally, ensure you are in the `REPO_ROOT/deployments/cognito/terraform` folder.

From the repository's root folder, run:
```sh
cd deployments/cognito/terraform
pwd
```

## Deployment Steps

### Configure

1. Register a domain using [Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html). 
    When you register a domain with Route 53, it automatically creates a hosted zone for the domain. 

    - The provided Terraform stack will create and delegate a subdomain for the Kubeflow platform automatically.
    - If you do not use Route53 for your top level domain, you can follow the steps in [create a subdomain section]({{< ref "../../add-ons/load-balancer/guide/#create-a-subdomain" >}}) of the load balancer guide to create a subdomain manually and provide the route 53 subdomain hosted zone name as input to the terraform stack. 
    Additionally you have to set the Terraform variable `create_subdomain=false`:
        ```sh
        export TF_VAR_create_subdomain="false"
        ```

1. Set the following environment variables:

    ```sh
    # Region to create the cluster in
    export CLUSTER_REGION=
    # Name of the cluster to create
    export CLUSTER_NAME=
    # Name of an existing Route53 root domain (e.g. example.com)
    export ROOT_DOMAIN=
    # Name of the subdomain to create (e.g. platform.example.com)
    export SUBDOMAIN=
    # Name of the cognito user pool to create
    export USER_POOL_NAME=
    # Load balancer scheme
    export LOAD_BALANCER_SCHEME=internet-facing
    
    ```
    > NOTE: Configure Load Balancer Scheme (e.g. `internet-facing` or `internal`). Default is set to `internet-facing`. Use `internal` as the load balancer scheme if you want the load balancer to be accessible only within your VPC. See [Load balancer scheme](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#load-balancer-scheme) in the AWS documentation

1. Save the variables to a `.tfvars` file:

    ```sh
    cat <<EOF > sample.auto.tfvars
    cluster_name="${CLUSTER_NAME}"
    cluster_region="${CLUSTER_REGION}"
    aws_route53_root_zone_name="${ROOT_DOMAIN}"
    aws_route53_subdomain_zone_name="${SUBDOMAIN}"
    cognito_user_pool_name="${USER_POOL_NAME}"
    load_balancer_scheme="${LOAD_BALANCER_SCHEME}"
    EOF
    ```

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.

### (Recommended) Configure AWS S3 to backup Terraform state
Optionally enable AWS S3 as a Terraform backend by following the instructions [here]({{< ref "/docs/deployment/terraform-s3-backend.md#" >}}).

### View all configurations

View [all possible configuration options of the terraform stack](https://github.com/awslabs/kubeflow-manifests/blob/main/deployments/cognito/terraform/variables.tf) in the `variables.tf` file.

### Preview
To check the configuration you are about to apply, run:
```sh
terraform init && terraform plan
```

### Apply
Deploy Kubeflow with Cognito:
```sh
make deploy
```

## Connect to your Kubeflow dashboard
1. Go to the Cognito console and [create some users]({{< ref "/docs/deployment/cognito/manifest/guide.md#60-connect-to-the-central-dashboard" >}})  in `Users and groups` using their email `user@example.com`.
1. Get the link to the central dashboard:
    ```sh
    terraform output -raw kubelow_platform_domain
    ```
1. Open the link in the browser and connect via the user credentials that were just configured.

## Cleanup

Uninstall Kubeflow on AWS. 
```sh
make delete
```
