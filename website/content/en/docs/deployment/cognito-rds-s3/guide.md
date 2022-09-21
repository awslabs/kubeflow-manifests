+++
title = "Manifest Deployment Guide"
description = "Deploying Kubeflow with Amazon Cognito, RDS and S3"
weight = 10
+++

This guide describes how to deploy Kubeflow on Amazon EKS using Cognito for your identity provider, RDS for your database, and S3 for your artifact storage.

## 1. Prerequisites
Refer to the [general prerequisites guide]({{< ref "/docs/deployment/prerequisites.md" >}}) and the [RDS and S3 setup guide]({{< ref "/docs/deployment/rds-s3/guide.md" >}}) in order to:
1. Install the CLI tools
2. Clone the repositories
3. Create an EKS cluster
4. Create an S3 Bucket
5. Create an RDS Instance
6. Configure AWS Secrets for RDS and S3
7. Install AWS Secrets and Kubernetes Secrets Store CSI driver
8. Configure an RDS endpoint and an S3 bucket name for Kubeflow Pipelines

## Configure Custom Domain and Cognito

1. Follow the [Cognito setup guide]({{< ref "/docs/deployment/cognito/guide.md" >}}) from [Section 1.0 (Custom domain)]({{< ref "/docs/deployment/cognito/guide.md#10-custom-domain-and-certificates" >}}) up to [Section 3.0 (Configure ingress)]({{< ref "/docs/deployment/cognito/guide.md#30-configure-ingress" >}}) in order to:
    1. Create a custom domain
    1. Create TLS certificates for the domain
    1. Create a Cognito Userpool
    1. Configure Ingress
2. Deploy Kubeflow.
    1. Install Kubeflow using the following command:
        {{< tabpane persistLang=false >}}
        {{< tab header="Kustomize" lang="toml" >}}
        make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito-rds-s3
        {{< /tab >}}
        {{< tab header="Helm" lang="yaml" >}}
        make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito-rds-s3
        {{< /tab >}}
        {{< /tabpane >}}
1. Follow the rest of the Cognito guide from [section 5.0 (Updating the domain with ALB address)]({{< ref "/docs/deployment/cognito/guide.md#50-updating-the-domain-with-alb-address" >}}) in order to:
    1. Add/Update the DNS records in a custom domain with the ALB address
    1. Create a user in a Cognito user pool
    1. Create a profile for the user from the user pool
    1. Connect to the central dashboard
