+++
title = "Uninstall Kubeflow"
description = "Delete Kubeflow deployments and Amazon EKS clusters"
weight = 30
+++

## Uninstall Kubeflow on AWS

First, delete all existing Kubeflow profiles. 

```bash
kubectl get profile
kubectl delete profile --all
```

Then, delete the Kubeflow deployment with the following command:

```bash
kustomize build example | kubectl delete -f 
```

Cleanup steps for specific deployment options can be found in their respective [installation directories](https://github.com/awslabs/kubeflow-manifests/tree/v1.3-branch/distributions/aws/examples). 

> Note: This will not delete your Amazon EKS cluster.

## (Optional) Delete Amazon EKS Cluster

If you created a dedicated Amazon EKS cluster for Kubeflow using `eksctl`, you can delete it with the following command:

```bash
eksctl delete cluster --region $CLUSTER_REGION --name $CLUSTER_NAME
```

> Note: It is possible that parts of the CloudFormation deletion will fail depending upon modifications made post-creation. In that case, manually delete the eks-xxx role in IAM, then the ALB, the EKS target groups, and the subnets of that particular cluster. Then, retry the command to delete the nodegroups and the cluster.

For more detailed information on deletion options, see [Deleting an Amazon EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html). 