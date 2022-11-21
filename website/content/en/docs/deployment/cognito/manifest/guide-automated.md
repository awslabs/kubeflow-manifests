+++
title = "Automated Deployment Guide"
description = "Deploying Kubeflow with AWS Cognito as identity provider using setup scripts"
weight = 10
+++

> Note: Helm installation option is still in preview.

This guide describes how to deploy Kubeflow on Amazon EKS using Cognito as your identity provider. Kubeflow uses Istio to manage internal traffic. In this guide, we will:

- create an Ingress to manage external traffic to the Kubernetes services
- create an Application Load Balancer (ALB) to provide public DNS
- enable TLS authentication for the Load Balancer
- create a custom domain to host Kubeflow (because the certificates needed for TLS are not supported for ALB's public DNS names)

## Prerequisites

This guide assumes you have Python 3.8 installed and that you have completed the [prerequisites]({{< ref "/docs/deployment/prerequisites.md" >}}).

## 1.0 Create the required resources

The following steps automate:

- the creation of a [custom domain and certificates]({{< ref "/docs/deployment/cognito/manifest/guide#10-create-a-custom-domain-and-certificates" >}}) as in section 1.0 of the Manual Deployment Guide to host Kubeflow and TLS certificates for the domain.
- the creation of a [Cognito Userpool]({{< ref "/docs/deployment/cognito/manifest/guide#20-create-a-cognito-user-pool" >}}) for user authentication.
- the [configuration of an ingress and load balancer controller manifests]({{< ref "/docs/deployment/cognito/manifest/guide.md#30-configure-ingress" >}}).

Each section is detailed in [Cognito Manual Deployment Guide]({{< ref "/docs/deployment/cognito/manifest/guide.md" >}}).

1. Install the dependencies for the scripts.
    ```shell
    pip install -r tests/e2e/requirements.txt
    ```
1. Update the following values in `tests/e2e/utils/cognito_bootstrap/config.yaml`:
    
    * The **registered root domain** informations in `route53.rootDomain`. 
    
        - In the yaml example below, `route53.rootDomain.name` is set to `example.com`.
       
        - If your domain is managed in route53, enter the **Hosted zone ID** found under `Hosted zone details` in `route53.rootDomain.hostedZoneId`. 
        Skip this step if your domain is managed by other domain provider.

    * The **name of the subdomain hosting Kubeflow** (e.g. `platform.example.com`) in `route53.subDomain.name`. Read [Create domain and certificates]({{< ref "/docs/add-ons/load-balancer/guide.md#create-domain-and-certificates" >}}) to understand why we use a subdomain.

    * The **cluster name and region** where kubeflow will be deployed in `cluster.name` and `cluster.region` (e.g. `us-west-2`) respectively.
        
    * The **name of Cognito userpool** in `cognitoUserpool.name` (e.g. kubeflow-users).

    * The **load balancer scheme** (e.g. `internet-facing` or `internal`). Default is set to `internet-facing`. Use `internal` as the load balancer scheme if you want the load balancer to be accessible only within your VPC. See [Load balancer scheme](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#load-balancer-scheme) in the AWS documentation for more details.

    The config file will look something like:
    ```yaml
    cognitoUserpool:
        name: kubeflow-users
    cluster:
        name: kube-eks-cluster
        region: us-west-2
    kubeflow:
        alb:
            scheme: internet-facing
    route53:
        rootDomain:
            hostedZoneId: XXXX
            name: example.com
        subDomain:
            name: platform.example.com
    ```
1. Run the following script to create the resources.
    ```shell
    cd tests/e2e
    PYTHONPATH=.. python utils/cognito_bootstrap/cognito_pre_deployment.py
    cd -
    ```
    The script will update the config file with the resource names, ids, and ARNs it created. It will look something like:

    ```yaml
    cognitoUserpool:
        ARN: arn:aws:cognito-idp:us-west-2:123456789012:userpool/us-west-2_yasI9dbxF
        appClientId: 5jmk7ljl2a74jk3n0a0fvj3l31
        domainAliasTarget: xxxxxxxxxx.cloudfront.net
        domain: auth.platform.example.com
        name: kubeflow-users
    kubeflow:
        alb:
            scheme: internet-facing
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

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide. 

## 2.0 Install Kubeflow

Install Kubeflow using the following command:
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< /tabpane >}}

## 3.0 Update the domain with ALB address
1. Check if ALB is provisioned. It takes about 3-5 minutes.
    ```shell
    kubectl get ingress -n istio-system
    Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
    NAME            CLASS    HOSTS   ADDRESS                                                              PORTS   AGE
    istio-ingress   <none>   *       k8s-istiosys-istioing-xxxxxx-110050202.us-west-2.elb.amazonaws.com   80      15d
    ```
    If `ADDRESS` is empty after a few minutes, check the logs of  the `alb-ingress-controller` by following this [troubleshooting guide]({{< ref "/docs/troubleshooting-aws.md#alb-fails-to-provision" >}}).

1. Substitute the ALB address under `kubeflow.alb.dns` in `tests/e2e/utils/cognito_bootstrap/config.yaml`. The kubeflow section of the config file will look like:
    ```yaml
    kubeflow:
        alb:
            dns: ebde55ee-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com
            serviceAccount:
                name: alb-ingress-controller
                policyArn: arn:aws:iam::123456789012:policy/alb_ingress_controller_kube-eks-clusterxxx
    ```

1. Run the following script to update the subdomain with the ALB address:
    ```shell
    cd tests/e2e
    PYTHONPATH=.. python utils/cognito_bootstrap/cognito_post_deployment.py
    cd -
    ```
## 4.0 Connect to Kubeflow central dashboard 
Follow the instructions in the [`Connecting to Kubeflow central dashboard`]({{< ref "/docs/deployment/cognito/manifest/guide#60-connect-to-the-central-dashboard" >}}) section of the Manual Deployment Guide to:

* Create a user in Cognito user pool.
* Create a profile for the user from the user pool.
* Connect to the central dashboard.

## 5.0 Uninstall Kubeflow

> Note: Delete all the resources you might have created in your profile namespaces before running these steps.

1. Run the following commands to delete the profiles:

   ```bash
    kubectl delete profiles --all
    ```

1. Delete the kubeflow deployment:

    {{< tabpane persistLang=false >}}
    {{< tab header="Kustomize" lang="toml" >}}
make delete-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito
    {{< /tab >}}
    {{< tab header="Helm" lang="yaml" >}}
make delete-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito
    {{< /tab >}}
    {{< /tabpane >}}
 
1. To delete the rest of the resources (subdomain, certificates etc.), run the following commands from the root of your repository:

    * Ensure you have the configuration file `tests/e2e/utils/cognito_bootstrap/config.yaml` updated by the `cognito_post_deployment.py` script. If you did not use the script, update the name, ARN, or ID of the resources that you created in a separate yaml file in `tests/e2e/utils/cognito_bootstrap/config.yaml` by referring to the following sample:

        ```yaml
        # Sample config file
        cognitoUserpool:
            ARN: arn:aws:cognito-idp:us-west-2:123456789012:userpool/us-west-2_yasI9dbxF
            appClientId: 5jmk7ljl2a74jk3n0a0fvj3l31
            domainAliasTarget: xxxxxxxxxx.cloudfront.net
            domain: auth.platform.example.com
            name: kubeflow-users
        kubeflow:
            alb:
                scheme: internet-facing
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
    * Run the following command to install the script dependencies and delete the resources:

        ```bash
        cd tests/e2e
        pip install -r requirements.txt
        PYTHONPATH=.. python utils/cognito_bootstrap/cognito_resources_cleanup.py
        cd -
        ```
        You can rerun the script in case some resources fail to delete.

