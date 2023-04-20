+++
title = "Configure AWS S3 as a backend for storing Terraform State"
description = "Backup terraform state to AWS S3"
weight = 70
+++

## Local vs. Remote state

While Terraform manages the state of resources it has created through a `terraform.tfstate` file, by default this file only exists locally.
This means that you will need to manually copy over the original `terraform.tfstate` file when managing previously created resources on a different host. Without having a local copy of the `terraform.tfstate` file, Terraform will attempt to recreate all the existing resource since it does not know their current state.

Having multiple copies of the same `terraform.tfstate` can become difficult to manage and keep in sync between different hosts and users.
Instead, by using a remote backend, such as AWS S3, state is consolidated in one shared remote location and can be re-used between multiple hosts. Additionally, the state will not be lost if the local `terraform.tfstate` file was accidentally deleted.

For additional details on using AWS S3 as a Terraform backend, refer to the following Terraform [documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3#s3).

> **Important**
>
> Required Terraform variables will still need to be provided as input when deploying even if a remote state file is being used.
>
> For example, a cluster name will still need to be provided through the TF_VAR_cluster_name or `.tfvar` file before deploying.
>
> Make sure you provide your .tfvars file in the deployment folder and export all the TF_VAR variables when making changes to an existing deployment.


## Permissions

The permissions required by the Terraform user to use AWS S3 as a Terraform backend can be found [here](https://developer.hashicorp.com/terraform/language/settings/backends/s3#s3-bucket-permissions).

## Creating an initial backup of Terraform state

1. Decide on a name and region for the bucket to create, as well as a path in the bucket for where to store the `tfstate` file.

1. Define the following environment variables:
    ```sh
    export S3_BUCKET_NAME=
    export PATH_TO_BACKUP=
    export BUCKET_REGION=
    ```

1. Create the S3 bucket:
    ```sh
    if [[ $BUCKET_REGION == "us-east-1" ]]; then
        aws s3api create-bucket --bucket ${S3_BUCKET_NAME} --region ${BUCKET_REGION}
    else
        aws s3api create-bucket --bucket ${S3_BUCKET_NAME} --region ${BUCKET_REGION} \
        --create-bucket-configuration LocationConstraint=${BUCKET_REGION}
    fi
    ```

1. Go to the respective Terraform deployment folder. For example, if Vanilla kubeflow is being deployed:
    ```sh
    cd deployments/vanilla/terraform
    ```

1. Create the following file:
    ```sh
    cat <<EOF > backend.tf
    terraform {
        backend "s3" {
            bucket = "${S3_BUCKET_NAME}"
            key    = "${PATH_TO_BACKUP}"
            region = "${BUCKET_REGION}"
        }
    }
    EOF
    ```

1. If you were following a Terraform deployment guide, resume following the guide to deploy Terraform using the above configuration. Otherwise, follow the respective Terraform deployment guide for your deployment type to apply the above configuration and deploy.

## Re-using a Terraform state backup

1. Find the name and region for the created bucket, as well as the path in the bucket for where the `tfstate` file is stored.

1. Define the following environment variables:
    ```sh
    export S3_BUCKET_NAME=
    export PATH_TO_BACKUP=
    export BUCKET_REGION=
    ```

1. Go to the respective Terraform deployment folder. For example, if Vanilla kubeflow is being deployed:
    ```sh
    cd deployments/vanilla/terraform
    ```

1. Create the following file:
    ```sh
    cat <<EOF > backend.tf
    terraform {
        backend "s3" {
            bucket = "${S3_BUCKET_NAME}"
            key    = "${PATH_TO_BACKUP}"
            region = "${BUCKET_REGION}"
        }
    }
    EOF
    ```

1. If you were following a Terraform deployment guide, resume following the guide to deploy Terraform using the above configuration. Otherwise, follow the respective Terraform deployment guide for your deployment type to apply the above configuration and deploy.