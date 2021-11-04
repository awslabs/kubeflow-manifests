# AWS Kubeflow Manifests

## Overview

In these manifest directories you can find example Kustomize manifests as well as instructions for installing Kubeflow components configured with supported AWS services.

## Provisioning AWS Resources 

### Create EKS Cluster

Run this command to create an EKS cluster by changing `<YOUR_CLUSTER_NAME>` and `<YOUR_CLUSTER_REGION>` to your preferred settings. More details about cluster creation via `eksctl` can be found [here](https://eksctl.io/usage/creating-and-managing-clusters/).

```
export CLUSTER_NAME=<YOUR_CLUSTER_NAME>
export CLUSTER_REGION=<YOUR_CLUSTER_REGION>

eksctl create cluster \
--name ${CLUSTER_NAME} \
--version 1.19 \
--region ${CLUSTER_REGION} \
--nodegroup-name linux-nodes \
--node-type m5.xlarge \
--nodes 5 \
--nodes-min 1 \
--nodes-max 10 \
--managed
```

## Install

### Components configured for RDS and S3
Installation steps can be found [here](rds-s3/README.md)

### Components configured for Cognito
Installation steps can be found [here](cognito/README.md)

