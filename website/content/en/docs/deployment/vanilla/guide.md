+++
title = "Manifest Deployment Guide"
description = "Deploy the vanilla version of Kubeflow on AWS using Kustomize or Helm"
weight = 20
+++

> Note: Helm installation option is still in preview.

This guide describes how to deploy Kubeflow on Amazon EKS. This vanilla version has minimal changes to the upstream Kubeflow manifests.

## Prerequisites

Be sure that you have satisfied the installation prerequisites before working through this guide. You need to:
- [Set up your deployment environment]({{< ref "prerequisites.md" >}})
- [Create an EKS Cluster]({{< ref "create-eks-cluster.md" >}})

## (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.


## Build Manifests and install Kubeflow

> ⚠️ Warning: We use a default email (`user@example.com`) and password (`12341234`) for our guides. For any production Kubeflow deployment, you should change the default password by following the steps in [Change default user password]({{< ref "../connect-kubeflow-dashboard#change-the-default-user-password-kustomize" >}}).

---

### Install with a single command

Install all Kubeflow official components (residing under `apps`) and all common services (residing under `common`) using either Kustomize or Helm with a single command:

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=vanilla
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=vanilla
{{< /tab >}}
{{< /tabpane >}}

### Connect to your Kubeflow cluster

After installation, it will take some time for all Pods to become ready. Make sure all Pods are ready before trying to connect, otherwise you might get unexpected errors. To check that all Kubeflow-related Pods are ready, use the following commands:

```sh
kubectl get pods -n cert-manager
kubectl get pods -n istio-system
kubectl get pods -n auth
kubectl get pods -n knative-eventing
kubectl get pods -n knative-serving
kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-user-example-com
```

### Connect to your Kubeflow Dashboard

You can now start experimenting and running your end-to-end ML workflows with Kubeflow on AWS!

For information on connecting to your Kubeflow dashboard depending on your deployment environment, see  [Connect to your Kubeflow Dashboard]({{< ref "connect-kubeflow-dashboard.md" >}}). 

### Uninstall Kubeflow on AWS

Uninstall Kubeflow on AWS with a single command. 
> Note: Make sure you have the correct INSTALLATION_OPTION and DEPLOYMENT_OPTION environment variables set for your chosen installation

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make delete-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=vanilla
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make delete-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=vanilla
{{< /tab >}}
{{< /tabpane >}}

> Note: This will not delete your Amazon EKS cluster.

### (Optional) Delete Amazon EKS cluster

If you created a dedicated Amazon EKS cluster for Kubeflow using `eksctl`, you can delete it with the following command:

```bash
eksctl delete cluster --region $CLUSTER_REGION --name $CLUSTER_NAME
```

For more detailed information on deletion options, see [Deleting an Amazon EKS cluster](https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html). 