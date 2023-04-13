+++
title = "Using AWS S3 as a backend for Terraform"
description = "Backup terraform state to AWS S3"
weight = 70
+++

## Local vs. Remote state

While Terraform manages the state of resources it has created through a `terraform.tfstate`, by default this file only exists locally.
This means that you will need to manually copy over the original `terraform.tfstate` file when managing previously created resources on a different host. 
This can become difficult to manage and keep in sync when multiple copies exist between different hosts and users.

By using a remote backend, such as AWS S3, state is consolidated in one shared remote location and can be re-used between multiple hosts. Additionally, the state will not be lost if the local `terraform.tfstate` file was accidentally deleted.

For additional details on using AWS S3 as a Terraform backend, refer to the following Terraform [documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3#s3).


## Permissions

The permissions required by the Terraform user to use AWS S3 as a Terraform backend can be found [here](https://developer.hashicorp.com/terraform/language/settings/backends/s3#s3-bucket-permissions).

## Creating an initial backup of Terraform state

1. Decide on a name and region for the bucket to create, as well as a path in the bucket for where to store the `tfstate` file.

1. Define the following environment variables:
    ```sh
    export BUCKET_NAME=
    export PATH_TO_BACKUP=
    export BUCKET_REGION=
    ```

1. Create the S3 bucket:
    ```sh
    aws s3api create-bucket --bucket ${BUCKET_NAME} --region ${BUCKET_REGION}
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
            bucket = "${BUCKET_NAME}"
            key    = "${PATH_TO_BACKUP}"
            region = "${BUCKET_REGION}"
        }
    }
    EOF
    ```

1. The above configuration will be used the next time Terraform is deployed.

## Restoring from a Terraform state backup

1. Find the name and region for the created bucket, as well as the path in the bucket for where the `tfstate` file is stored.

1. Define the following environment variables:
    ```sh
    export BUCKET_NAME=
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
            bucket = "${BUCKET_NAME}"
            key    = "${PATH_TO_BACKUP}"
            region = "${BUCKET_REGION}"
        }
    }
    EOF
    ```

1. The above configuration will be used the next time Terraform is deployed.