+++
title = "Create an EKS Cluster"
description = "Create an EKS cluster before you deploy Kubeflow on AWS using Kustomize or Helm"
weight = 15
+++

> Note : You do not need to create an EKS cluster if you are using Terraform

## Create EKS Cluster using `eksctl`

> Note: Be sure to check [Amazon EKS and Kubeflow Compatibility]({{< ref "/docs/about/eks-compatibility.md" >}}) when creating your cluster with specific EKS versions.

You can create a customized EKS cluster with the following steps.

> Note: Various controllers use IAM roles for service accounts (IRSA). An [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) must exist for your cluster to use IRSA.

Change the values for the `CLUSTER_NAME` and `CLUSTER_REGION` environment variables: 
```bash
export CLUSTER_NAME=$CLUSTER_NAME
export CLUSTER_REGION=$CLUSTER_REGION
```

Run the following command to create an EKS cluster:
```bash
eksctl create cluster \
--name ${CLUSTER_NAME} \
--version 1.25 \
--region ${CLUSTER_REGION} \
--nodegroup-name linux-nodes \
--node-type m5.xlarge \
--nodes 5 \
--nodes-min 5 \
--nodes-max 10 \
--managed \
--with-oidc
```

If you are using an existing EKS cluster, create an [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) and associate it with for your EKS cluster with the following command:
```bash
eksctl utils associate-iam-oidc-provider --cluster ${CLUSTER_NAME} \
--region ${CLUSTER_REGION} --approve
```

#### **Important:** If you are using an EKS version `>= 1.23` install the Amazon EBS CSI driver by following the instructions [here](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html).

More details about cluster creation via `eksctl` can be found in the [Creating and managing clusters](https://eksctl.io/usage/creating-and-managing-clusters/) guide.