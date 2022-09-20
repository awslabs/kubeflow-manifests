+++
title = "Terraform Deployment Guide"
description = "Deploy the vanilla distribution of Kubeflow on AWS using Terraform"
weight = 30
+++

> Note: Terraform deployment options are still in preview.

## Background

This guide will walk you through using Terraform to:
- Create a VPC
- Create an EKS cluster
- Deploy the vanilla distribution of Kubeflow on AWS

Terraform documentation can be found [here](https://www.terraform.io/docs).

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-ubuntu-environment" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-repository" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#create-ubuntu-environment" >}})

Additionally, ensure you are in the `REPO_ROOT/deployments/vanilla/terraform` folder.

If you are in repository's root folder, run:
```sh
cd deployments/vanilla/terraform
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
```

Save the variables to a `.tfvars` file:
```sh
cat <<EOF > sample.auto.tfvars
cluster_name="${CLUSTER_NAME}"
cluster_region="${CLUSTER_REGION}"
EOF
```

### Full Configuration

A full list of inputs for the terraform stack can be found here and in the `variables.tf` file:

| Name                 | Description                                       | Type   | Default  | Required |
|----------------------|---------------------------------------------------|--------|----------|----------|
| cluster_name         | Name of the cluster                               | string |          | Yes      |
| cluster_region       | Region to create the cluster                      | string |          | Yes      |
| eks_version          | The EKS version to use                            | string | 1.22     | No       |
| enable_aws_telemetry | Enable AWS telemetry component                    | bool   | true     | No       |
| kf_helm_repo_path    | Full path to the location of the helm repo for KF | string | ../../.. | No       |

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
