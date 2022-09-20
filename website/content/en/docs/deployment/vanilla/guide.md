+++
title = "Manifest Deployment Guide"
description = "Deploy the vanilla distribution of Kubeflow on AWS using Kustomize or Helm"
weight = 20
+++

This guide describes how to deploy Kubeflow on Amazon EKS. This vanilla version has minimal changes to the upstream Kubeflow manifests.

## Prerequisites

Be sure that you have satisfied the installation prerequisites before working through this guide. You need to:
- [Set up your deployment environment]({{< ref "prerequisites.md" >}})
- [Create an EKS Cluster]({{< ref "create-eks-cluster.md" >}})

## Build Manifests and install Kubeflow

> ⚠️ Warning: We use a default email (`user@example.com`) and password (`12341234`) for our guides. For any production Kubeflow deployment, you should change the default password by following the steps in [Change default user password]({{< ref "../connect-kubeflow-dashboard#change-the-default-user-password-kustomize" >}}).

---
**NOTE**

`kubectl apply` commands may fail on the first try. This is inherent in how Kubernetes and `kubectl` work (e.g., CR must be created after CRD becomes ready). The solution is to re-run the command until it succeeds. For the single-line command, we have included a bash one-liner to retry the command.

---

### Install with a single command

Install all Kubeflow official components (residing under `apps`) and all common services (residing under `common`) using either Kustomize or Helm with a single command:

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kf-vanilla
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=vanilla
{{< /tab >}}
{{< /tabpane >}}

### Connect to your Kubeflow Dashboard

You can now start experimenting and running your end-to-end ML workflows with Kubeflow on AWS!

For information on connecting to your Kubeflow dashboard depending on your deployment environment, see  [Connect to your Kubeflow Dashboard]({{< ref "connect-kubeflow-dashboard.md" >}}). 

### Uninstall Kubeflow on AWS

Uninstall Kubeflow on AWS with a single command. 

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make delete-kubeflow 
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make delete-kubeflow DEPLOYMENT_OPTION=rds-s3
{{< /tab >}}
{{< /tabpane >}}

> Note: This will not delete your Amazon EKS cluster.

### (Optional) Delete Amazon EKS cluster

If you created a dedicated Amazon EKS cluster for Kubeflow using `eksctl`, you can delete it with the following command:

```bash
eksctl delete cluster --region $CLUSTER_REGION --name $CLUSTER_NAME
```

For more detailed information on deletion options, see [Deleting an Amazon EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html). 