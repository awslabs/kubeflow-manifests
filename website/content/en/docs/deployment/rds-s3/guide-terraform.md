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

Define the following environment variables:
```sh
export TF_VAR_cluster_name=<desired_cluster_name>
export TF_VAR_cluster_region=<desired_cluster_region>
export TF_VAR_s3_bucket=<desired_s3_bucket>
export TF_VAR_db_instance_name=<desired_db_instance_name>
export TF_VAR_db_subnet_group_name=<desired_subnet_group_name>
export TF_VAR_minio_aws_access_key_id=<desired_minio_aws_access_key_id>
export TF_VAR_minio_aws_secret_access_key=<desired_minio_aws_secret_access_key>
export TF_VAR_rds_secret_name=<desired_rds_secret_name>
export TF_VAR_s3_secret_name=<desired_s3_secret_name>
```

### RDS and S3
Run the following command:
```sh
cd deployments/rds-s3/terraform
make deploy
```

### RDS only
```sh
cd deployments/rds-s3/rds-only/terraform
make deploy
```

### S3 only
```sh
cd deployments/rds-s3/s3-only/terraform
make deploy
```

## Connect to your Kubeflow dashboard

For information on connecting to your Kubeflow dashboard depending on your deployment environment, see [Port-forward (Terraform deployment)]({{< ref "../connect-kubeflow-dashboard/#port-forward-terraform-deployment" >}}). Then, [log into the Kubeflow UI]({{< ref "../connect-kubeflow-dashboard/#log-into-the-kubeflow-ui" >}}).

## Cleanup

Uninstall Kubeflow on AWS with a single command. 
```sh
make delete
```
