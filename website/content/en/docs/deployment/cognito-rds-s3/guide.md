+++
title = "Manifest Deployment Guide"
description = "Deploying Kubeflow with Amazon Cognito, RDS and S3"
weight = 10
+++

> Note: Helm installation option is still in preview.

This guide describes how to deploy Kubeflow on Amazon EKS using Cognito for your identity provider, RDS for your database, and S3 for your artifact storage.

## Prerequisites
Refer to the [general prerequisites guide]({{< ref "/docs/deployment/prerequisites" >}}) and the [RDS and S3 setup guide]({{< ref "/docs/deployment/rds-s3/guide" >}}) in order to:
1. Install the CLI tools
2. Clone the repositories
3. Create an EKS cluster
4. Create an S3 Bucket
5. Create an RDS Instance
6. Configure AWS Secrets or IAM Role for S3
7. Configure AWS Secrets for RDS
8. Install AWS Secrets and Kubernetes Secrets Store CSI driver
9. Configure an RDS endpoint and an S3 bucket name for Kubeflow Pipelines

## Configure Custom Domain and Cognito

1. Follow the Section 2.0 of [Cognito setup guide]({{< ref "/docs/deployment/cognito/manifest/guide-automated#20-create-required-resources" >}}) in order to:
    1. Create a custom domain
    1. Create TLS certificates for the domain
    1. Create a Cognito Userpool
    1. Configure Ingress

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.

2. Deploy Kubeflow.

    1. Export your pipeline-s3-credential-option
    {{< tabpane persistLang=false >}}
{{< tab header="IRSA" lang="toml" >}}
# Pipeline S3 Credential Option to configure 
export PIPELINE_S3_CREDENTIAL_OPTION="irsa"
{{< /tab >}}
{{< tab header="IAM User" lang="toml" >}}
# Pipeline S3 Credential Option to configure 
export PIPELINE_S3_CREDENTIAL_OPTION="static"
{{< /tab >}}
   {{< /tabpane >}}

    1. Install Kubeflow using the following command:

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito-rds-s3 PIPELINE_S3_CREDENTIAL_OPTION=$PIPELINE_S3_CREDENTIAL_OPTION
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito-rds-s3 PIPELINE_S3_CREDENTIAL_OPTION=$PIPELINE_S3_CREDENTIAL_OPTION
{{< /tab >}}
{{< /tabpane >}}

1. Follow the rest of the Cognito guide from [section 5.0 (Updating the domain with ALB address)]({{< ref "/docs/deployment/cognito/manifest/guide#50-update-the-domain-with-the-alb-address" >}}) in order to:

    1. Add/Update the DNS records in a custom domain with the ALB address
    1. Create a user in a Cognito user pool
    1. Create a profile for the user from the user pool
    1. Connect to the central dashboard

## Creating Profiles
A default profile named `kubeflow-user-example-com` for email `user@example.com` has been configured with this deployment. If you are using IRSA as `PIPELINE_S3_CREDENTIAL_OPTION`, any additional profiles that you create will also need to be configured with IRSA and S3 Bucket access. Follow the [pipeline profiles]({{< ref "/docs/deployment/create-profiles-with-iam-role.md" >}}) for instructions on how to create additional profiles.

If you are not using this feature, you can create a profile by just specifying email address of the user.

## Uninstall Kubeflow
> Note: Delete all the resources you might have created in your profile namespaces before running these steps.
1. Run the following commands to delete the profiles, ingress and corresponding ingress managed load balancer
   ```bash
    kubectl delete profiles --all
    ```

1. Delete the kubeflow deployment:
 
    {{< tabpane persistLang=false >}}
    {{< tab header="Kustomize" lang="toml" >}}make delete-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito-rds-s3 PIPELINE_S3_CREDENTIAL_OPTION=$PIPELINE_S3_CREDENTIAL_OPTION
    {{< /tab >}}
    {{< tab header="Helm" lang="yaml" >}}make delete-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito-rds-s3 PIPELINE_S3_CREDENTIAL_OPTION=$PIPELINE_S3_CREDENTIAL_OPTION
    {{< /tab >}}
    {{< /tabpane >}}

1. To delete the rest of resources (subdomain, certificates etc.), run the following commands from the root of your repository:

     * Ensure you have the configuration file `tests/e2e/utils/cognito_bootstrap/config.yaml` updated by the `cognito_post_deployment.py` script.. If you did not use the script, update the name, ARN, or ID of the resources that you created in a yaml file in `tests/e2e/utils/cognito_bootstrap/config.yaml` by referring to the following sample:

        ```yaml
        cognitoUserpool:
            ARN: arn:aws:cognito-idp:us-west-2:123456789012:userpool/us-west-2_yasI9dbxF
            appClientId: 5jmk7ljl2a74jk3n0a0fvj3l31
            domainAliasTarget: xxxxxxxxxx.cloudfront.net
            domain: auth.platform.example.com
            name: kubeflow-users
        kubeflow:
            alb:
                serviceAccount:
                    name: alb-ingress-controller
                    namespace: kubeflow
                    policyArn: arn:aws:iam::123456789012:policy/alb_ingress_controller_kube-eks-clusterxxx
        cluster:  
            name: kube-eks-cluster
            region: us-west-2
        route53:
            rootDomain:
                certARN: arn:aws:acm:us-east-1:123456789012:certificate/9d8c4bbc-3b02-4a48-8c7d-d91441c6e5af
                hostedZoneId: XXXXX
                name: example.com
            subDomain:
                us-west-2-certARN: arn:aws:acm:us-west-2:123456789012:certificate/d1d7b641c238-4bc7-f525-b7bf-373cc726
                hostedZoneId: XXXXX
                name: platform.example.com
                us-east-1-certARN: arn:aws:acm:us-east-1:123456789012:certificate/373cc726-f525-4bc7-b7bf-d1d7b641c238
        ```
    - Run the following command to install the script dependencies and delete the resources:
        ```bash
        cd tests/e2e
        pip install -r requirements.txt
        PYTHONPATH=.. python utils/cognito_bootstrap/cognito_resources_cleanup.py
        cd -
        ```
        You can rerun the script in case some resources fail to delete

1. To delete the rest of RDS-S3 resources:

     Make sure that you have the configuration file created by the script in `tests/e2e/utils/rds-s3/metadata.yaml`.
     ```bash
     PYTHONPATH=.. python utils/rds-s3/auto-rds-s3-cleanup.py
     ```  

