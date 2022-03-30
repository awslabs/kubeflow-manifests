# Exposing Kubeflow over Load Balancer

This tutorial shows how to expose Kubeflow over an external load balancer on AWS.

## Background

Kubeflow does not offer a generic solution for connecting to Kubeflow over a load balancer because this process is highly dependent on your environment/cloud provider. On AWS, we use the [AWS Load Balancer controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) which satisfies the Kubernetes [Ingress resource](https://kubernetes.io/docs/concepts/services-networking/ingress/) to create an [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html) (ALB). When you create a Kubernetes `Ingress`, an ALB is provisioned that load balances application traffic.

In order to connect to Kubeflow using a LoadBalancer, we need to setup HTTPS. The reason is that many of the Kubeflow web apps (e.g., Tensorboard Web App, Jupyter Web App, Katib UI) use [Secure Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies), so accessing Kubeflow with HTTP over a non-localhost domain does not work.

To secure the traffic and use HTTPS, we must associate a Secure Sockets Layer/Transport Layer Security (SSL/TLS) certificate with the load balancer. [AWS Certificate Manager](https://aws.amazon.com/certificate-manager/) is a service that lets you easily provision, manage, and deploy public and private Secure Sockets Layer/Transport Layer Security (SSL/TLS) certificates for use with AWS services and your internal connected resources. To create a certificate for use with the load balancer, you must specify a domain name i.e. certificates cannot be created for ALB DNS. You can register your domain using any domain service provider such as [Route53](https://aws.amazon.com/route53/), GoDoddy etc.

## Before you begin

Follow this guide only if you are **not** using `Cognito` as the authentication provider in your deployment. Cognito integrated deployment is configured with AWS Load Balancer controller by default to create an ingress managed application load balancer and exposes Kubeflow via a hosted domain.

## Prerequisites

1. Kubeflow deployment with Dex as auth provider(default in Vanilla Kubeflow).

## 1.0 Configure Ingress and Setup load balancer

As explained in the [background](#background), 
1. A registered domain. You can register a new domain or re-use an existing a domain. Follow the [section 1.0(Custom Domain)](../../cognito/README.md#10-custom-domain) of the guide to create a domain for hosting Kubeflow. Lets assume you created platform.example.com
1. 


by configuring an [Ingress](https://kubernetes.io/docs/user-guide/ingress) and using the AWS Load Balancer Controller to create an ingress managed [Application Load Balancer](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html).

identify and establish encrypted network connections over


## Create required resources and deploy ingress managed load balancer

1. The following steps automate:
    - creating a custom domain to host Kubeflow
    - TLS certificates for the domain using ACM
    - Configuring ingress and load balancer controller manifests
    - Building manifests and deploying the required components
    - Updating the domain with ALB address


    1. Install dependencies for the scripts
        ```
        pip install -r tests/e2e/requirements.txt
        ```
    1. Substitute values in `tests/e2e/utils/load_balancer/config.yaml`.
        1. Registed root domain in `route53.rootDomain.name`. Lets assume this domain is `example.com`
            1. If your domain is managed in route53, enter the Hosted zone ID found under Hosted zone details in `route53.rootDomain.hostedZoneId`. Skip this step if your domain is managed by other domain provider.
        1. Name of the sudomain you want to host Kubeflow (e.g. `platform.example.com`) in `route53.subDomain.name`. Please read [this section](./README.md#10-custom-domain) to understand why we use a subdomain.
        1. Cluster name and region where kubeflow will be deployed in `cluster.name` and `cluster.region` (e.g. us-west-2) respectively.
        1. The config file will look something like:
            1. ```
                cluster:
                    name: kube-eks-cluster
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
            cd tests/e2e
            PYTHONPATH=.. python utils/load_balancer/setup_load_balancer.py
            cd -
            ```
    1. The script will update the config file with the resource names/ids/ARNs it created. It will look something like:
        1. ```
            kubeflow:
                alb:
                    dns: ebde55ee-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com
                    serviceAccount:
                        name: alb-ingress-controller
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

    1. The central dashboard should now be available at [https://kubeflow.platform.example.com](https://kubeflow.platform.example.com/).