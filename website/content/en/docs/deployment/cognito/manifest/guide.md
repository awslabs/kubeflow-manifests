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

## 1.0 Create a custom domain and certificates

1. Follow the [Create a subdomain]({{< ref "/docs/add-ons/load-balancer/guide.md#create-a-subdomain" >}}) section of the Load Balancer guide to create a subdomain(e.g. `platform.example.com`) for hosting Kubeflow.
1. Follow the [Create certificates for domain]({{< ref "/docs/add-ons/load-balancer/guide.md#create-certificates-for-domain" >}}) section of the Load Balancer guide to create certificates required for TLS.

From this point onwards, we will be creating/updating the DNS records **in the subdomain only**. All the screenshots of the hosted zone in the following sections/steps of this guide are for the subdomain.

## 2.0 Create a Cognito User Pool

1. Create a user pool in Cognito in the same region as your EKS cluster. Type a pool name and choose `Review defaults`.
1. The **email** is a required user attribute since Kubeflow uses email address as the user identifier for multi-user isolation. See [Kubeflow documentation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation) for more information. On the review page, make sure **email** is selected as a required attribute. If it is not by default, edit the `Required attributes` and select `email`.

    ![cognito-email-required](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-email-required.png)

1. On the Configure sign-up experience page, unselect `Enable self-registration` under `Self-service sign-up?` and save changes. This step is optional but is recommended to have strict control over the users.

1. Click on `Create pool` to create the user pool.

1. Add an `App client` with any name and the default options.

    ![cognito-app-client-id](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-app-client-id.png)

1. In the `App client edit the Hosted UI`, select `Authorization code grant` flow under OAuth-2.0 and check `email`, `openid`, `aws.cognito.signin.user.admin` and `profile` scopes. 
Check also `Enabled Identity Providers`. 

    * Substitute `example.com` in this URL - `https://kubeflow.platform.example.com/oauth2/idpresponse` with your domain and use it as the Callback URL(s).

    * Substitute `example.com` in this URL - `https://kubeflow.platform.example.com` with your domain and use it as the Sign out URL(s).

        ![cognito-app-client-settings](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-app-client-settings.png)

        ![cognito-app-client-settings](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-app-client-settings-oidc.png)

1. Add a custom domain to the user pool. In order to add a custom domain to your user pool, you need to specify a domain name, and provide a certificate managed with AWS Certificate Manager (ACM).

    * In order to use a custom domain, its root(i.e. `platform.example.com`) must have an valid A type record. Create a new record of type `A` in the `platform.example.com` hosted zone with an arbitrary IP for now. Once the ALB created, we will update this value.
    
        Following is a screenshot of a `platform.example.com` hosted zone showing a record. 

        ![subdomain-initial-A-record](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-initial-A-record.png)

    * If your cluster is not in N.Virginia (us-east-1), [create an ACM certificate]({{< ref "/docs/add-ons/load-balancer/guide#create-certificates-for-domain" >}}) in us-east-1 for `*.platform.example.com`. That is because [Cognito requires](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html) a certificate in N.Virginia in order to have a custom domain for a user pool.

    * In the `Domain name`:
        
        * Choose `Use your domain`, type `auth.platform.example.com` and select the `*.platform.example.com` AWS managed certificate you’ve created in N.Virginia. Creating domain takes up to 15 mins.

            ![cognito-active-domain](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-active-domain.png)

        * When it’s created, it will return the `Alias target` CloudFront address.
                 
            ![cognito-domain-cloudfront-url](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-url.png)

        *  Create a new record of type `A` for `auth.platform.example.com` with the value of the CloudFront URL.

        * Select the `alias` toggle and select `Alias to Cloudfront distribution` for creating the record:

            ![cognito-domain-cloudfront-A-record-creating](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-A-record-creatin.png)

        * Following is a screenshot of a A record for `auth.platform.example.com` in the `platform.example.com` hosted zone:

            ![cognito-domain-cloudfront-A-record-created](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-domain-cloudfront-A-record-created.png)

## 3.0 Configure Ingress

1. Take note of the following values from the previous steps:

    * The **Pool ARN** of the user pool found in Cognito general settings.

    * The **App client id**, found in Cognito App clients.

    * The **Custom user pool domain** (e.g. `auth.platform.example.com`), found in the Cognito domain name.

    * The **ARN of the certificate** from the Certificate Manager in the region where your platform (for the subdomain) is running.

    * **SignOutURL** is the domain that you provided as the Sign out URL(s).

    * **CognitoLogoutURL** is comprised of your CognitoUserPoolDomain, CognitoAppClientId, and the domain that you provided as the Sign out URL(s).

    * The **load balancer scheme** (e.g. `internet-facing` or `internal`). Default is set to `internet-facing`. Use `internal` as the load balancer scheme if you want the load balancer to be accessible only within your VPC. See [Load balancer scheme](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/how-elastic-load-balancing-works.html#load-balancer-scheme) in the AWS documentation for more details.


1. Export those values:
    ```bash
    export CognitoUserPoolArn="<YOUR_USER_POOL_ARN>"
    export CognitoAppClientId="<YOUR_APP_CLIENT_ID>"
    export CognitoUserPoolDomain="<YOUR_USER_POOL_DOMAIN>"
    export certArn="<YOUR_ACM_CERTIFICATE_ARN>"
    export signOutURL="<YOUR_SIGN_OUT_URL>"
    export CognitoLogoutURL="https://$CognitoUserPoolDomain/logout?client_id=$CognitoAppClientId&logout_uri=$signOutURL"
    export loadBalancerScheme=internet-facing
    ```

1. The following commands will inject those values in a configuration file for setting up Ingress:

    Select the package manager of your choice.
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
yq e '.alb.scheme = env(loadBalancerScheme)' -i charts/common/ingress/cognito/values.yaml
    {{< /tab >}}
    {{< /tabpane >}}

1. The following commands will inject those values in a configuration file for setting up AWS authservice:

    Select the package manager of your choice.
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

1. Follow the [Configure Load Balancer Controller]({{< ref "/docs/add-ons/load-balancer/guide.md#configure-load-balancer-controller" >}}) section of the load balancer guide to setup the resources required by the load balancer controller.

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide.

## 4.0 Build the manifests and deploy Kubeflow

{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=cognito
{{< /tab >}}
{{< /tabpane >}}

## 5.0 Update the domain with the ALB address

1. Check if the ALB is provisioned. This may take a few minutes.

    ```bash
    kubectl get ingress -n istio-system
    Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
    NAME            CLASS    HOSTS   ADDRESS                                                              PORTS   AGE
    istio-ingress   <none>   *       k8s-istiosys-istioing-xxxxxx-110050202.us-west-2.elb.amazonaws.com   80      15d
    ```
    If `ADDRESS` is empty after a few minutes, see [ALB fails to provision]({{< ref "/docs/troubleshooting-aws.md#alb-fails-to-provision" >}}) in the troubleshooting guide.

1. When the ALB is ready, copy the DNS name of the load balancer and create a CNAME entry for it in Route53 under the subdomain (`platform.example.com`) for `*.platform.example.com`

    ![subdomain-*.platform-and-*.default-records](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-*.platform-and-*.default-records.png)

1. Update the type `A` record created for `platform.example.com` using ALB DNS name. Change from `127.0.0.1` to the ALB DNS name. You have to use the alias form under `Alias to application and classical load balancer` then select a region and your ALB address.

    ![subdomain-A-record-updated](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-A-record-updated.png)

1. Here is a screenshot of all the record sets in the hosted zone for reference.

    ![subdomain-records-summary](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/subdomain-records-summary.png)

## 6.0 Connect to the central dashboard

1. The central dashboard should now be available at `https://kubeflow.platform.example.com`. 

    Before connecting to the dashboard:

    * Go to the Cognito console and create some users in `Users and groups`. These are the users who will log in to the central dashboard.
        - Create a user with email address `user@example.com`. This user and email address come preconfigured and have a Profile created by default.
    ![cognito-user-pool-created](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/cognito/cognito-user-pool-created.png)
    * Create a Profile for a user by following the steps in the [Manual Profile Creation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation). 
    The following is a Profile example for reference:
         ```bash
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

1. Open the central dashboard at `https://kubeflow.platform.example.com`. 
It will redirect to Cognito for login. Use the credentials of a user you just created in the previous steps.

> Note: It might take a few minutes for the DNS changes to propagate and for your URL to work. 
Check if the DNS entry propogated with the [Google Admin Toolbox](https://toolbox.googleapps.com/apps/dig/#CNAME/).

## 7.0 Uninstall Kubeflow

To delete the resources created in this guide, refer to the [Uninstall section in Automated Cognito deployment guide]({{< ref "/docs/deployment/cognito/manifest/guide-automated.md#50-uninstall-kubeflow" >}}).
