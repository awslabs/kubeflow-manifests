# Deploying Kubeflow with AWS Cognito as idP

This guide describes how to deploy Kubeflow on AWS EKS using Cognito as identity provider. Kubeflow uses Istio to manage internal traffic. In this guide we will be creating an Ingress to manage external traffic to the Kubernetes services and an Application Load Balancer(ALB) to provide public DNS and enable TLS authentication at the load balancer. We will also be creating a custom domain to host Kubeflow since certificates(needed for TLS) for ALB's public DNS names are not supported.

## Prerequisites

This guide assumes you have python3 installed and completed the pre-requisites from this [README](./README.md#prerequisites).

## Create required resources and deploy Kubeflow

1. The following steps automate [section 1.0(Custom Domain)](./README.md#10-custom-domain), [section 2.0(certificates)](./README.md#20-certificate) and [section 3.0(Cognito user pool)](./README.md#30-cognito-user-pool) of the cognito guide to create a custom domain to host Kubeflow, TLS certificates for the domain and create a Cognito Userpool respectively.
    1. Install dependencies for the scripts
        ```
        pip install -r distributions/aws/test/e2e/requirements.txt
        ```
    1. Substitute values in `distributions/aws/test/e2e/utils/cognito_bootstrap/config.yaml`.
        1. Registed root domain in `route53.rootDomain.name`. Lets assume this domain is `example.com`
            1. If your domain is managed in route53, enter the Hosted zone ID found under Hosted zone details in `route53.rootDomain.hostedZoneId`. Skip this step if your domain is managed by other domain provider.
        1. Name of the sudomain you want to host Kubeflow (e.g. `platform.example.com`) in `route53.subDomain.name`. Please read [this section](./README.md#10-custom-domain) to understand why we use a subdomain.
        1. Region where kubeflow will be deployed (i.e. cluster region) in `kubeflow.region` e.g. us-west-2.
        1. Name of cognito userpool in `cognitoUserpool.name` e.g. kubeflow-users.
        1. The config file will look something like:
            1. ```
                cognitoUserpool:
                    name: kubeflow-users
                kubeflow:
                    region: us-west-2
                route53:
                    rootDomain:
                        hostedZoneId: XXXX
                        name: example.com
                    subDomain:
                        name: platform.example.com
                ```
    1. Run the script to create the resources
        1. ```
            cd distributions/aws/test/e2e
            PYTHONPATH=.. python utils/cognito_bootstrap/cognito_pre_deployment.py
            cd -
            ```
    1. The script will update the config file with the resource names/ids/ARNs it created. It will look something like:
        1. ```
            cognitoUserpool:
                ARN: arn:aws:cognito-idp:us-west-2:123456789012:userpool/us-west-2_yasI9dbxF
                appClientId: 5jmk7ljl2a74jk3n0a0fvj3l31
                domainAliasTarget: xxxxxxxxxx.cloudfront.net
                domain: auth.platform.example.com
                name: kubeflow-users
            kubeflow:
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
        1. Use the values `cognitoUserpool.ARN`, `cognitoUserpool.appClientId`, `cognitoUserpool.domain` and `subdomain.us-west-2-certARN` (i.e. certificate ARN of subdomain in the region where cluster is) from config file in the next step.

1. Follow the [section 4.0(Configure Ingress)](./README.md#40-configure-ingress) of [this guide](./README.md) to configure Ingress

1. Follow the [section 5.0(Building manifests and deploying Kubeflow)](./README.md#50-building-manifests-and-deploying-kubeflow) to install Kubeflow

1. Updating the domain with ALB address
    1. Check if ALB is provisioned. It takes around 3-5 minutes
        1. ```
            kubectl get ingress -n istio-system
            Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
            NAME            CLASS    HOSTS   ADDRESS                                                                  PORTS   AGE
            istio-ingress   <none>   *       ebde55ee-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com   80      15d
            ```
        2. If `ADDRESS` is empty after a few minutes, check the logs of alb-ingress-controller by following [this guide](https://www.kubeflow.org/docs/distributions/aws/troubleshooting-aws/#alb-fails-to-provision)
    1. Substitute the ALB address under `kubeflow.ALBDNS` in `distributions/aws/test/e2e/utils/cognito_bootstrap/config.yaml`. The kubeflow section of the config file will look like:
        1. ```
            kubeflow:
                ALBDNS: ebde55ee-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com
                region: us-west-2
            ```
    1. Run the following script to update the subdomain with ALB address
        1. ```
            cd distributions/aws/test/e2e
            PYTHONPATH=.. python utils/cognito_bootstrap/cognito_post_deployment.py
            cd -
            ```
1. Follow the rest of the cognito guide from [section 7.0(Connecting to central dashboard)](./README.md#70-connecting-to-central-dashboard) to:
    1. Create a user in Cognito user pool
    1. Create a profile for the user from the user pool
    1. Connect to the central dashboard
