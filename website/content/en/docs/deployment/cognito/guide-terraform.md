+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with AWS Cognito as an identity provider using Terraform"
weight = 30
+++

> Note: Terraform deployment options are still in preview.

## Background

This guide will walk you through using Terraform to:
- Create a VPC
- Create an EKS cluster
- Create a Route53 subdomain
- Create a Cognito user pool
- Deploy Kubeflow with Cognito as an identity provider

Additional background on using Cognito with the AWS Distribution for Kubeflow can be found [here]({{< ref "./guide.md/#background" >}}).

Terraform documentation can be found [here](https://www.terraform.io/docs).

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#create-ubuntu-environment" >}})

Additionally, ensure you are in the `REPO_ROOT/deployments/cognito/terraform` folder.

If you are in repository's root folder, run:
```sh
cd deployments/cognito/terraform
pwd
```

## Deployment Steps

### Configure

Define the following environment variables:
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
```

Save the variables to a `.tfvars` file:
```sh
cat <<EOF > sample.auto.tfvars
cluster_name="${CLUSTER_NAME}"
cluster_region="${CLUSTER_REGION}"
aws_route53_root_zone_name="${ROOT_DOMAIN}"
aws_route53_subdomain_zone_name="${SUBDOMAIN}"
cognito_user_pool_name="${USER_POOL_NAME}"
create_subdomain="true"
EOF
```

### Full Configuration

A full list of inputs for the terraform stack can be found in the `variables.tf` file.

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
