+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with RDS and S3 using Terraform"
weight = 30
+++

> Note: Terraform deployment options are still in preview.

## Background

This guide will walk you through using Terraform to:
- Create a VPC
- Create an EKS cluster
- Create a S3 bucket
- Create an RDS DB instance
- Deploy Kubeflow with RDS as a KFP and Katib persistence layer and S3 as an artifact store

Terraform documentation can be found [here](https://www.terraform.io/docs).

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#install-necessary-tools" >}})


Additionally, ensure you are in the `REPO_ROOT/deployments/rds-s3/terraform` folder.

If you are in repository's root folder, run:
```sh
cd deployments/rds-s3/terraform
pwd
```

## Deployment Steps

### Configure

1. Define the following environment variables:

    ```bash
    # Region to create the cluster in
    export CLUSTER_REGION=
    # Name of the cluster to create
    export CLUSTER_NAME=
    # true/false flag to configure and deploy with RDS
    export USE_RDS="true"
    # true/false flag to configure and deploy with S3
    export USE_S3="true"
    ```

As of Kubeflow 1.7, there are two options to configure Amazon S3 as an artifact store for pipelines. Choose one of the following options:
  >  Note: IRSA is only supported in KFPv1, if you plan to use KFPv2, choose the IAM User option. IRSA support for KFPv2 will be added in the next release.
   -  Option 1 - IRSA (Recommended): IAM Role for Service Account (IRSA) which allows the use of AWS IAM permission boundaries at the Kubernetes pod level. A Kubernetes service account (SA) is associated with an IAM role with a role policy that scopes the IAM permissions (e.g. S3 read/write access, etc.). When a pod in the SA namespace is annotated with the SA name, EKS injects the IAM role ARN and a token is used to get the credentials so that the pod can make requests to AWS services within the scope of the role policy associated with the IRSA.
   For more information, see [Amazon EKS IAM roles for service accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html). 

   - Option 2 - IAM User (Deprecated):
      [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_cliwpsapi) with permissions to get bucket locations and allow read and write access to objects in an S3 bucket where you want to store the Kubeflow artifacts. Take note of the AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY of the IAM user that you created to use in the following step, which will be referenced as `minio_aws_access_key_id` and `minio_aws_secret_access_key` respectively.

1. Export your desired PIPELINE_S3_CREDENTIAL_OPTION specific values
{{< tabpane persistLang=false >}}
{{< tab header="IRSA" lang="toml" >}}
# Pipeline S3 Credential Option to configure 
export PIPELINE_S3_CREDENTIAL_OPTION="irsa"
{{< /tab >}}
{{< tab header="IAM User" lang="toml" >}}
# Pipeline S3 Credential Option to configure 
export PIPELINE_S3_CREDENTIAL_OPTION="static"
# AWS access key id of the static credentials used to authenticate the Minio Client
export TF_VAR_minio_aws_access_key_id=
# AWS secret access key of the static credentials used to authenticate the Minio Client
export TF_VAR_minio_aws_secret_access_key=
{{< /tab >}}
   {{< /tabpane >}}

1. Save the variables to a `.tfvars` file:

    ```sh
    cat <<EOF > sample.auto.tfvars
    cluster_name="${CLUSTER_NAME}"
    cluster_region="${CLUSTER_REGION}"
    generate_db_password="true"
    use_rds="${USE_RDS}"
    use_s3="${USE_S3}"
    pipeline_s3_credential_option="${PIPELINE_S3_CREDENTIAL_OPTION}"


    # The below values are set to make cleanup easier but are not recommended for production
    deletion_protection="false"
    secret_recovery_window_in_days="0"
    force_destroy_s3_bucket="true"
    EOF
    ```

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.

### (Recommended) Configure AWS S3 to backup Terraform state
Optionally enable AWS S3 as a Terraform backend by following the instructions [here]({{< ref "/docs/deployment/terraform-s3-backend.md#" >}}).

### All Configurations

A full list of inputs for the terraform stack can be found [here](https://github.com/awslabs/kubeflow-manifests/blob/main/deployments/rds-s3/terraform/variables.tf).

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

## Creating Profiles
A default profile named `kubeflow-user-example-com` for email `user@example.com` has been configured with this deployment. If you are using IRSA as `PIPELINE_S3_CREDENTIAL_OPTION`, any additional profiles that you create will also need to be configured with IRSA and S3 Bucket access. Follow the [pipeline profiles]({{< ref "/docs/deployment/create-profiles-with-iam-role.md" >}}) for instructions on how to create additional profiles.

If you are not using this feature, you can create a profile by just specifying email address of the user.

## Connect to your Kubeflow dashboard

For information on connecting to your Kubeflow dashboard depending on your deployment environment, see [Port-forward (Terraform deployment)]({{< ref "../connect-kubeflow-dashboard/#port-forward-terraform-deployment" >}}). Then, [log into the Kubeflow UI]({{< ref "../connect-kubeflow-dashboard/#log-into-the-kubeflow-ui" >}}).

## Cleanup

Uninstall Kubeflow on AWS with a single command. 
```sh
make delete
```
