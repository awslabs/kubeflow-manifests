+++
title = "Custom OIDC IDP"
description = "Deploying Kubeflow with custom OpenID Connect (OIDC) identity provider"
weight = 65
+++

This guide describes how to deploy Kubeflow on Amazon EKS using external identity provider (idP) that supports OIDC standard. Similar to [Cognito tutorial]({{< ref "/docs/deployment/cognito/guide.md" >}}).

In this guide, we will configure Application Load Balancer (ALB) to authenticate users that access Kubeflow. This approach has some benefits:

1. You can use your existing auth provider.
2. You don't have to pay for Cognito. 
3. You can use this to deploy Kubeflow on AWS Region that doesn't support Cognito or ALB integration with Cognito.

Note that ALB supports authentication only with Cognito or OIDC based idP. For any other type of idP like SAML, LDAP, or Microsoft AD and Social idPs it still need to be done via Cognito.

## Prerequisites
Check to make sure that you have the necessary [prerequisites]({{< ref "/docs/deployment/prerequisites.md" >}}).

## Background 

Read the [background section]({{< ref "/docs/deployment/add-ons/load-balancer/guide.md#background" >}}) in the Load Balancer guide for information on the requirements for exposing Kubeflow over a Load Balancer.

Read the [create domain and certificate section]({{< ref "/docs/deployment/add-ons/load-balancer/guide.md#create-domain-and-certificates" >}}) for information on why we use a subdomain for hosting Kubeflow.

## 1.0 Custom domain and certificates

1. Follow the [Create a subdomain]({{< ref "/docs/deployment/add-ons/load-balancer/guide.md#create-a-subdomain" >}}) section of the Load Balancer guide to create a subdomain(e.g. `platform.example.com`) for hosting Kubeflow.
1. Follow the [Create certificates for domain]({{< ref "/docs/deployment/add-ons/load-balancer/guide.md#create-certificates-for-domain" >}}) section of the Load Balancer guide to create certificates required for TLS.

From this point onwards, we will be creating/updating the DNS records **only in the subdomain**. All the screenshots of the hosted zone in the following sections/steps of this guide are for the subdomain.

## 2.0 Configure OIDC idP

If you already have an existing ODIC idP, following are the details you will need from your idP to configure it:

1. Issuer Endpoint
2. Authorization Endpoint
3. Token Endpoint
4. UserInfo Endpoint
5. ClientId and Client Secret for your App in idP

Otherwise, you can create a sample OIDC idP with [Auth0](https://manage.auth0.com/).

### (Optional) 2.1 Example configure Auth0 for idP

1. Go to [Auth0](https://manage.auth0.com/) and sign up or login.
1. From the getting started page, choose the dropdown menu on the navbar, and choose **Create tenant**.

    ![auth0-getting-started](../../../images/oidc-idp/auth0-getting-started.png)

1. Enter tenant name, and choose **Create**.

    ![auth0-new-tenant](../../../images/oidc-idp/auth0-new-tenant.png)

1. From left sidebar, choose **Applications**, **Default App**. Make sure you are on **Settings** tab, then take note of the `Domain`, `Client ID`, and `Client Secret` from **Basic Information** panel.

    ![auth0-app-info](../../../images/oidc-idp/auth0-app-info.png) 

1. Scroll down to **Application URIs** panel, enter the following information:
    1. Allowed Callback URLs: https://kubeflow.{your-subdomain}/oauth2/idpresponse, example: `https://kubeflow.platform.example.com/oauth2/idpresponse`
    2. Allowed Logout URLs: https://kubeflow.{your-subdomain}, example: `https://kubeflow.platform.example.com`

1. Scroll down and choose **Save Changes**.

## 3.0 Configure Ingress

1. Export values from the previous step. For cert ARN, use ARN of the certificate from the Certificate Manager in the region where your platform (for the subdomain) is running. Replace the example `kfaws.au.auth0.com` and `https://kubeflow.platform.example.com` below with your own domain, and use your own client ID and client secret:

    ```bash
    export IssuerEndpoint="https://kfaws.au.auth0.com/"
    export AuthorizationEndpoint="https://kfaws.au.auth0.com/authorize"
    export TokenEndpoint="https://kfaws.au.auth0.com/oauth/token"
    export UserInfoEndpoint="https://kfaws.au.auth0.com/userinfo"
    export LogoutEndpoint="https://kfaws.au.auth0.com/v2/logout?client_id=<YOUR_CLIENT_ID>&returnTo=https://kubeflow.platform.example.com"
    export ClientID="<YOUR_CLIENT_ID>"
    export ClientSecret="<YOUR_CLIENT_SECRET>"
    export certArn="<YOUR_ACM_CERTIFICATE_ARN>"
    ```

    You can refer to [Auth0 docs](https://auth0.com/docs/api/authentication) for each endpoint info.

1. Substitute values for setting up Ingress.
    ```bash
      printf '
      certArn='$certArn'
      oidcIssuer='$IssuerEndpoint'
      oidcAuthorizationEndpoint='$AuthorizationEndpoint'
      oidcTokenEndpoint='$TokenEndpoint'
      oidcUserInfoEndpoint='$UserInfoEndpoint'
      ' > awsconfigs/common/istio-ingress/overlays/oidc/params.env
      ```

      ```bash
      printf '
      clientID='$ClientID'
      clientSecret='$ClientSecret'
      ' > awsconfigs/common/istio-ingress/overlays/oidc/secrets.env
      ```

1. Substitute values for setting up AWS authservice.
    ```bash
    printf '
    LOGOUT_URL='$LogoutEndpoint'
    ' > awsconfigs/common/aws-authservice/base/params.env
    ```

1. Follow steps 1-4 in the [Configure Load Balancer Controller]({{< ref "/docs/deployment/add-ons/load-balancer/guide.md#configure-load-balancer-controller" >}}) section of the load balancer guide to setup the resources required the load balancer controller.

1. Open `awsconfigs/common/aws-alb-ingress-controller/base/load_balancer_controller.yaml`. Remove the following lines:
    ```bash
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      labels:
        app.kubernetes.io/component: controller
        app.kubernetes.io/name: aws-load-balancer-controller
      name: aws-load-balancer-controller
      namespace: kube-system
    ---
    ```

## 4.0 Building manifests and deploying Kubeflow

Install individual components:

```bash
# Run per section, reapply manifest if you see an error

# Kubeflow namespace
kustomize build upstream/common/kubeflow-namespace/base | kubectl apply -f -

# Kubeflow Roles
kustomize build upstream/common/kubeflow-roles/base | kubectl apply -f -

# Cert-Manager
kustomize build upstream/common/cert-manager/cert-manager/base | kubectl apply -f -
kustomize build upstream/common/cert-manager/kubeflow-issuer/base | kubectl apply -f -

# Istio
kustomize build upstream/common/istio-1-14/istio-crds/base | kubectl apply -f -
kustomize build upstream/common/istio-1-14/istio-namespace/base | kubectl apply -f -
kustomize build awsconfigs/common/istio | kubectl apply -f -

# KNative
kustomize build upstream/common/knative/knative-serving/overlays/gateways | kubectl apply -f -
kustomize build upstream/common/knative/knative-eventing/base | kubectl apply -f -
kustomize build upstream/common/istio-1-14/cluster-local-gateway/base | kubectl apply -f -

# Kubeflow Istio Resources
kustomize build upstream/common/istio-1-14/kubeflow-istio-resources/base | kubectl apply -f -

# Kubeflow Pipelines
kustomize build awsconfigs/apps/pipeline/base | kubectl apply -f -

# Katib
kustomize build upstream/apps/katib/upstream/installs/katib-with-kubeflow | kubectl apply -f -

# Central Dashboard
kustomize build upstream/apps/centraldashboard/upstream/overlays/kserve | kubectl apply -f -

# Notebooks
kustomize build awsconfigs/apps/jupyter-web-app | kubectl apply -f -
kustomize build upstream/apps/jupyter/notebook-controller/upstream/overlays/kubeflow | kubectl apply -f -

# Admission Webhook
kustomize build upstream/apps/admission-webhook/upstream/overlays/cert-manager | kubectl apply -f -

# Profiles + KFAM
kustomize build upstream/apps/profiles/upstream/overlays/kubeflow | kubectl apply -f -

# Volumes Web App
kustomize build upstream/apps/volumes-web-app/upstream/overlays/istio | kubectl apply -f -

# Tensorboard
kustomize build upstream/apps/tensorboard/tensorboards-web-app/upstream/overlays/istio | kubectl apply -f -
kustomize build upstream/apps/tensorboard/tensorboard-controller/upstream/overlays/kubeflow | kubectl apply -f -

# Training Operator
kustomize build upstream/apps/training-operator/upstream/overlays/kubeflow | kubectl apply -f -

# AWS Telemetry - This is an optional component. See usage tracking documentation for more information
kustomize build awsconfigs/common/aws-telemetry | kubectl apply -f -

# KServe
kustomize build awsconfigs/apps/kserve | kubectl apply -f -
kustomize build upstream/contrib/kserve/models-web-app/overlays/kubeflow | kubectl apply -f -

# Ingress
kustomize build awsconfigs/common/istio-ingress/overlays/oidc | kubectl apply -f -

# ALB controller
kustomize build awsconfigs/common/aws-alb-ingress-controller/base | kubectl apply -f -

# AWS Authservice
kustomize build awsconfigs/common/aws-authservice/base | kubectl apply -f -
```

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
1. Open the central dashboard at `https://kubeflow.platform.example.com`. It will redirect to your idP page for login. Use the credentials of the user that you just created a Profile for in previous step.
> Note: It might a few minutes for DNS changes to propagate and for your URL to work. Check if the DNS entry propogated with the [Google Admin Toolbox](https://toolbox.googleapps.com/apps/dig/#CNAME/)

## 7.0 Uninstall Kubeflow

To delete the resources created in this guide, run the commands in step `Building manifests and deploying Kubeflow` in reverse order, and change `kubectl apply -f -` with `kubectl delete -f -`. 

```bash
# AWS Authservice
kustomize build awsconfigs/common/aws-authservice/base | kubectl delete -f -

# Delete other components in reverse order...
...

# Kubeflow namespace
kustomize build upstream/common/kubeflow-namespace/base | kubectl delete -f -
```
