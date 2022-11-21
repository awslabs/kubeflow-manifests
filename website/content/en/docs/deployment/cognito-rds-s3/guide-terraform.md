+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with Cognito, RDS, and S3 using Terraform"
weight = 30
+++

> Note: Terraform deployment options are still in preview.

## Background

This guide will walk you through using Terraform to:
- Create a VPC
- Create an EKS cluster
- Create a Route53 subdomain
- Create a Cognito user pool
- Create a S3 bucket
- Create an RDS DB instance
- Deploy Kubeflow with Cognito as an identity provider, RDS as a KFP and Katib persistence layer, and S3 as an artifact store

Find additional information on [using Cognito with the AWS Distribution for Kubeflow]({{< ref "./guide/#background" >}}) in this guide. You can also check [Terraform documentation](https://www.terraform.io/docs).

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#install-necessary-tools" >}})

Additionally, ensure you are in the `REPO_ROOT/deployments/cognito-rds-s3/terraform` folder.

If you are in repository's root folder, run:
```sh
cd deployments/cognito-rds-s3/terraform
pwd
```

## Deployment Steps

### Configure

1. Register a domain using [Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html). When you register a domain with Route 53, it automatically creates a hosted zone for the domain. 
    - The provided Terraform stack will create and delegate a subdomain for the Kubeflow platform automatically.
    - If you do not use Route53 for your top level domain, you can follow the steps in [create a subdomain section]({{< ref "../../add-ons/load-balancer/guide/#create-a-subdomain" >}}) of load balancer guide to create a subdomain manually and provide the route 53 subdomain hosted zone name as input to the terraform stack. 
        - Additionally you have to set the Terraform variable `create_subdomain=false`:
            ```sh
            export TF_VAR_create_subdomain="false"
            ```

1. Create an IAM user to use with the Minio Client

    [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_cliwpsapi) with permissions to get bucket locations and allow read and write access to objects in an S3 bucket where you want to store the Kubeflow artifacts. Take note of the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY of the IAM user that you created to use in the following step, which will be referenced as `TF_VAR_minio_aws_access_key_id` and `TF_VAR_minio_aws_secret_access_key` respectively.

1. Define the following environment variables:

    ```sh
    # Region to create the cluster in
    export CLUSTER_REGION=
    # Name of the cluster to create
    export CLUSTER_NAME=
    # AWS access key id of the static credentials used to authenticate the Minio Client
    export TF_VAR_minio_aws_access_key_id=
    # AWS secret access key of the static credentials used to authenticate the Minio Client
    export TF_VAR_minio_aws_secret_access_key=
    # Name of an existing Route53 root domain (e.g. example.com)
    export ROOT_DOMAIN=
    # Name of the subdomain to create (e.g. platform.example.com)
    export SUBDOMAIN=
    # Name of the cognito user pool to create
    export USER_POOL_NAME=
    # true/false flag to configure and deploy with RDS
    export USE_RDS="true"
    # true/false flag to configure and deploy with S3
    export USE_S3="true"
    # true/false flag to configure and deploy with Cognito
    export USE_COGNITO="true"
    # Load Balancer Scheme
    export LOAD_BALANCER_SCHEME=internet-facing
    ```

    > NOTE: Configure Load Balancer Scheme (e.g. `internet-facing` or `internal`). Default is set to `internet-facing`. Use `internal` as the load balancer scheme if you want the load balancer to be accessible only within your VPC. See [Load balancer scheme](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#load-balancer-scheme) in the AWS documentation

1. Save the variables to a `.tfvars` file:
    ```sh
    cat <<EOF > sample.auto.tfvars
    cluster_name="${CLUSTER_NAME}"
    cluster_region="${CLUSTER_REGION}"
    generate_db_password="true"
    aws_route53_root_zone_name="${ROOT_DOMAIN}"
    aws_route53_subdomain_zone_name="${SUBDOMAIN}"
    cognito_user_pool_name="${USER_POOL_NAME}"
    use_rds="${USE_RDS}"
    use_s3="${USE_S3}"
    use_cognito="${USE_COGNITO}"
    load_balancer_scheme="${LOAD_BALANCER_SCHEME}"

    # The below values are set to make cleanup easier but are not recommended for production
    deletion_protection="false"
    secret_recovery_window_in_days="0"
    force_destroy_s3_bucket="true"
    EOF
    ```

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.

### View all Configurations

View [all possible configuration options of the terraform stack](https://github.com/awslabs/kubeflow-manifests/blob/main/deployments/cognito-rds-s3/terraform/variables.tf) in the `variables.tf` file.

### Preview

View a preview of the configuration you are about apply:
```sh
terraform init && terraform plan
```

### Apply

Run the following command:
```sh
make deploy
```

## Connect to your Kubeflow dashboard

1. Head over to your user pool in the Cognito console and create a user with email `user@example.com` in `Users and groups`. 
1. Get the link to the central dashboard:
    ```sh
    terraform output -raw kubelow_platform_domain
    ```
1. Open the link in the browser and connect via the user credentials that were just configured.

## Cleanup

Uninstall Kubeflow on AWS with a single command. 
```sh
make delete
```
