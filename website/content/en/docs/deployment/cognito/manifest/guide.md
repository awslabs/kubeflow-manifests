+++
title = "Manual Deployment Guide"
description = "Deploying Kubeflow with AWS Cognito as identity provider using Kustomize or Helm"
weight = 20
+++

> Note: Helm installation option is still in preview.

This guide describes how to deploy Kubeflow on Amazon EKS using Cognito as your identity provider. Kubeflow uses Istio to manage internal traffic. In this guide, we will:
- create an Ingress to manage external traffic to the Kubernetes services
- create an Application Load Balancer (ALB) to provide public DNS
- enable TLS authentication for the Load Balancer
- create a custom domain to host Kubeflow (because the certificates needed for TLS are not supported for ALB's public DNS names)

## Prerequisites
Check to make sure that you have the necessary [prerequisites]({{< ref "/docs/deployment/prerequisites.md" >}}).

## Background 

Read the [background section]({{< ref "/docs/add-ons/load-balancer/guide.md#background" >}}) in the Load Balancer guide for information on the requirements for exposing Kubeflow over a Load Balancer.

Read the [create domain and certificate section]({{< ref "/docs/add-ons/load-balancer/guide.md#create-domain-and-certificates" >}}) for information on why we use a subdomain for hosting Kubeflow.

## (Optional) Automated setup
The rest of the sections in this guide walk you through each step for setting up domain, certificates, and a Cognito userpool using the AWS Console. This guide is intended for a new user to understand the design and details of these setup steps. If you prefer to use automated scripts and avoid human error for setting up the resources for deploying Kubeflow with Cognito, follow the [automated setup guide]({{< ref "/docs/deployment/cognito/manifest/guide-automated.md" >}}).

## 1.0 Custom domain and certificates

1. Follow the [Create a subdomain]({{< ref "/docs/add-ons/load-balancer/guide.md#create-a-subdomain" >}}) section of the Load Balancer guide to create a subdomain(e.g. `platform.example.com`) for hosting Kubeflow.
1. Follow the [Create certificates for domain]({{< ref "/docs/add-ons/load-balancer/guide.md#create-certificates-for-domain" >}}) section of the Load Balancer guide to create certificates required for TLS.

From this point onwards, we will be creating/updating the DNS records **only in the subdomain**. All the screenshots of the hosted zone in the following sections/steps of this guide are for the subdomain.

## 2.0 Cognito User Pool

1. Create a user pool in Cognito in the same region as your EKS cluster. Type a pool name and choose `Review defaults`.
1. Email is a required user attribute since Kubeflow uses email address as the user identifier for multi-user isolation. See this [documentation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation) for example. On the review page, make sure email is selected as a required attribute. If it is not by default, Edit the `Required attributes` and select `email`.
    1. ![cognito-email-required](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-email-required.png)
1. On the Policies page, select `Only allow administrators to create users` under `Do you want to allow users to sign themselves up?` and save changes. This step is optional but is recommended to have strict control over the users.
1. Click on `Create pool` to create the user pool.
1. Add an `App client` with any name and the default options.
    1. ![cognito-app-client-id](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-app-client-id.png)
1. In the `App client settings`, select `Authorization code grant` flow under OAuth-2.0 and check box `email`, `openid`, `aws.cognito.signin.user.admin` and `profile` scopes. Also check box `Enabled Identity Providers`. 
    1. Substitute `example.com` in this URL - `https://kubeflow.platform.example.com/oauth2/idpresponse` with your domain and use it as the Callback URL(s).
    2. Substitute `example.com` in this URL - `https://kubeflow.platform.example.com` with your domain and use it as the Sign out URL(s).
    3. ![cognito-app-client-settings](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-app-client-settings.png)
1. Add a custom domain to the user pool. In order to add a custom domain to your user pool, you need to specify a domain name, and provide a certificate managed with AWS Certificate Manager (ACM).
    1. In order to use a custom domain, its root(i.e. `platform.example.com`) must have an valid A type record. Create a new record of type `A` in `platform.example.com` hosted zone with an arbitrary IP for now. Once we have ALB created, we will update this value.
        1. Following is a screenshot of `platform.example.com` hosted zone. A record is shown. 
            1. ![subdomain-initial-A-record](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-initial-A-record.png)
    1. If your cluster is not in N.Virginia(us-east-1), create an ACM certificate in us-east-1 for `*.platform.example.com` by following the process similar to [section 2.0]({{< ref "/docs/add-ons/load-balancer/guide.md#create-certificates-for-domain" >}}). That is because [Cognito requires](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html) a certificate in N.Virginia in order to have a custom domain for a user pool.
    1. In the `Domain name` choose `Use your domain`, type `auth.platform.example.com` and select the `*.platform.example.com` AWS managed certificate you’ve created in N.Virginia. Creating domain takes up to 15 mins.
        1. ![cognito-active-domain](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-active-domain.png)
        2. When it’s created, it will return the `Alias target` CloudFront address.
            1. Screenshot of the CloudFront URL for Cognito Domain name:
                1. ![cognito-domain-cloudfront-url](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-url.png)
            2.  Create a new record of type `A` for `auth.platform.example.com` with the value of the CloudFront URL.
                1. Select the `alias` toggle and select Alias to Cloudfront distribution for creating the record
                2. ![cognito-domain-cloudfront-A-record-creating](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-A-record-creatin.png)
                3. Following is a screenshot of the A record for `auth.platform.example.com` in `platform.example.com` hosted zone:
                    1. ![cognito-domain-cloudfront-A-record-created](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-A-record-created.png)

## 3.0 Configure Ingress

1. Take note of the following values from the previous step
    1. The Pool ARN of the user pool found in Cognito general settings.
    1. The App client id, found in Cognito App clients.
    1. The custom user pool domain (e.g. `auth.platform.example.com`), found in the Cognito domain name.
    1. The ARN of the certificate from the Certificate Manager in the region where your platform (for the subdomain) is running.
    1. signOutURL is the domain that you provided as the Sign out URL(s).
    1. CognitoLogoutURL is comprised of your CognitoUserPoolDomain, CognitoAppClientId, and your domain that you provided as the Sign out URL(s).
    1. LoadBalancerScheme (e.g. `internet-facing` or `internal`). Default is set to `internet-facing`. Use `internal` as the load balancer schema if you want the load balancer to be accessible only within your VPC. See [Load balancer scheme](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#load-balancer-scheme) in the AWS documentation for more details.
    1. Export the values:
        1. 
          ```bash
          export CognitoUserPoolArn="<YOUR_USER_POOL_ARN>"
          export CognitoAppClientId="<YOUR_APP_CLIENT_ID>"
          export CognitoUserPoolDomain="<YOUR_USER_POOL_DOMAIN>"
          export certArn="<YOUR_ACM_CERTIFICATE_ARN>"
          export signOutURL="<YOUR_SIGN_OUT_URL>"
          export CognitoLogoutURL="https://$CognitoUserPoolDomain/logout?client_id=$CognitoAppClientId&logout_uri=$signOutURL"
          export loadBalancerScheme=internet-facing
          ```
1. Substitute values for setting up Ingress.

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
printf '
CognitoUserPoolArn='$CognitoUserPoolArn'
CognitoAppClientId='$CognitoAppClientId'
CognitoUserPoolDomain='$CognitoUserPoolDomain'
certArn='$certArn'
' > awsconfigs/common/istio-ingress/overlays/cognito/params.env
printf '
loadBalancerScheme='$loadBalancerScheme'
' > awsconfigs/common/istio-ingress/base/params.env
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
yq e '.alb.certArn = env(certArn)' -i charts/common/ingress/cognito/values.yaml
yq e '.alb.cognito.UserPoolArn = env(CognitoUserPoolArn)' -i charts/common/ingress/cognito/values.yaml
yq e '.alb.cognito.UserPoolDomain = env(CognitoUserPoolDomain)' -i charts/common/ingress/cognito/values.yaml
yq e '.alb.cognito.appClientId = env(CognitoAppClientId)' -i charts/common/ingress/cognito/values.yaml
yq e '.alb.scheme = env(loadBalancerScheme) -i charts/common/ingress/cognito/values.yaml
{{< /tab >}}
{{< /tabpane >}}


1. Substitute values for setting up AWS authservice.
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
printf '
LOGOUT_URL='$CognitoLogoutURL'
' > awsconfigs/common/aws-authservice/base/params.env
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
yq e '.LOGOUT_URL = env(CognitoLogoutURL)' -i charts/common/aws-authservice/values.yaml
{{< /tab >}}
{{< /tabpane >}}

1. Follow the [Configure Load Balancer Controller]({{< ref "/docs/add-ons/load-balancer/guide.md#configure-load-balancer-controller" >}}) section of the load balancer guide to setup the resources required the load balancer controller.

## 4.0 Building manifests and deploying Kubeflow

1. Install with a single command:
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< /tabpane >}}

## 5.0 Updating the domain with ALB address

1. Check if ALB is provisioned. This may take a few minutes.
    1. ```bash
        kubectl get ingress -n istio-system
        Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
        NAME            CLASS    HOSTS   ADDRESS                                                              PORTS   AGE
        istio-ingress   <none>   *       k8s-istiosys-istioing-xxxxxx-110050202.us-west-2.elb.amazonaws.com   80      15d
        ```
    2. If `ADDRESS` is empty after a few minutes, see [ALB fails to provision]({{< ref "/docs/troubleshooting-aws.md#alb-fails-to-provision" >}}) in the troubleshooting guide.
1. When ALB is ready, copy the DNS name of that load balancer and create a CNAME entry to it in Route53 under subdomain (`platform.example.com`) for `*.platform.example.com`
    1. ![subdomain-*.platform-and-*.default-records](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-*.platform-and-*.default-records.png)
1. Update the type `A` record created in section for `platform.example.com` using ALB DNS name. Change from `127.0.0.1` → ALB DNS name. You have to use alias form under `Alias to application and classical load balancer` and select region and your ALB address.
    1. ![subdomain-A-record-updated](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-A-record-updated.png)
1. Screenshot of all the record sets in hosted zone for reference
    1. ![subdomain-records-summary](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-records-summary.png)

## 6.0 Connecting to central dashboard

1. The central dashboard should now be available at `https://kubeflow.platform.example.com`. Before connecting to the dashboard:
    1. Head over to the Cognito console and create some users in `Users and groups`. These are the users who will log in to the central dashboard.
        1. ![cognito-user-pool-created](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-user-pool-created.png)
    1. Create a Profile for a user by following the steps in the [Manual Profile Creation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation). The following is an example Profile for reference:
        1. ```bash
            apiVersion: kubeflow.org/v1beta1
            kind: Profile
            metadata:
                # replace with the name of profile you want, this will be user's namespace name
                name: namespace-for-my-user
                namespace: kubeflow
            spec:
                owner:
                    kind: User
                    # replace with the email of the user
                    name: my_user_email@kubeflow.com
            ```
1. Open the central dashboard at `https://kubeflow.platform.example.com`. It will redirect to Cognito for login. Use the credentials of the user that you just created a Profile for in previous step.
> Note: It might a few minutes for DNS changes to propagate and for your URL to work. Check if the DNS entry propogated with the [Google Admin Toolbox](https://toolbox.googleapps.com/apps/dig/#CNAME/)

## 7.0 Uninstall Kubeflow

To delete the resources created in this guide, refer to the [Uninstall section in Automated Cognito deployment guide]({{< ref "/docs/deployment/cognito/manifest/guide-automated.md#uninstall-kubeflow" >}})
