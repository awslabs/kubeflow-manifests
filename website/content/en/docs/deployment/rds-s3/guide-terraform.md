+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with RDS and S3 using Terraform"
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

Ensure you are in the `REPO_ROOT/deployments/rds-s3/terraform` folder.

### Configure

Define the following environment variables:
```sh
# Region to create the cluster in
export CLUSTER_REGION=
# Name of the cluster to create
export CLUSTER_NAME=
# AWS access key id of the static credentials used to authenticate the Minio Client
export MINIO_AWS_ACCESS_KEY_ID=
# AWS secret access key of the static credentials used to authenticate the Minio Client
export MINIO_AWS_SECRET_ACCESS_KEY=
# true/false flag to configure and deploy with RDS
export USE_RDS="true"
# true/false flag to configure and deploy with S3
export USE_S3="true"
```

Save the variables to a `.tfvars` file:
```sh
cat <<EOF > sample.auto.tfvars
cluster_name="${CLUSTER_NAME}"
cluster_region="${CLUSTER_REGION}"
minio_aws_access_key_id="${MINIO_AWS_ACCESS_KEY_ID}"
minio_aws_secret_access_key="${MINIO_AWS_SECRET_ACCESS_KEY}"
generate_db_password="true"
use_rds="${USE_RDS}"
use_s3="${USE_S3}"

# The below values are set to make cleanup easier but are not recommended for production
deletion_protection="false"
secret_recovery_window_in_days="0"
force_destroy_s3_bucket="true"
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

For information on connecting to your Kubeflow dashboard depending on your deployment environment, see [Port-forward (Terraform deployment)]({{< ref "../connect-kubeflow-dashboard/#port-forward-terraform-deployment" >}}). Then, [log into the Kubeflow UI]({{< ref "../connect-kubeflow-dashboard/#log-into-the-kubeflow-ui" >}}).

## Cleanup

Uninstall Kubeflow on AWS with a single command. 
```sh
make delete
```
