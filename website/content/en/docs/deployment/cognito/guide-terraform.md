+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with AWS Cognito as identity provider using Terraform"
weight = 30
+++

> Note: Terraform deployment options are still in preview.

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#create-ubuntu-environment" >}})

## Deployment Steps

### Directory

Ensure you are in the `REPO_ROOT/deployments/cognito/terraform` folder.

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

1. Head over to your user pool in the Cognito console and create some users in `Users and groups`. These are the users who will log in to the central dashboard.
    1. ![cognito-user-pool-created](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-user-pool-created.png)
1. Create a Profile for a user by following the steps in the [Manual Profile Creation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation). The following is an example Profile for reference:
    1. ```bash
        apiVersion: kubeflow.org/v1beta1
        kind: Profile
        metadata:
            # replace with the name of profile you want, this will be user's namespace name
            name: namespace-for-my-user
            namespace: kubeflow
        spec:
            owner:
                kind: User
                # replace with the email of the user
                name: my_user_email@kubeflow.com
        ```
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
