# Deploying Kubeflow with AWS Cognito as idP

This guide describes how to deploy Kubeflow on AWS EKS using Cognito as identity provider. Kubeflow uses Istio to manage internal traffic. In this guide we will be creating an Ingress to manage external traffic to the Kubernetes services and an Application Load Balancer(ALB) to provide public DNS and enable TLS authentication at the load balancer. We will also be creating a custom domain to host Kubeflow since certificates(needed for TLS) for ALB's public DNS names are not supported.

## Prerequisites
Follow the pre-requisites section from [this guide](../prerequisites.md)

## Background 

Read the [background section](../add-ons/load-balancer/README.md#background) in the load balancer guide for information on the requirements for exposing Kubeflow over a load balancer.

Read the [create domain and cerificate section](../add-ons/load-balancer/README.md#create-domain-and-certificates) for information on why we use subdomain for hosting Kubeflow.

## (Optional) Automated setup
The rest of the sections in this guide walks you through each step for setting up domain, certificates and Cognito userpool using AWS Console and is good for a new user to understand the design and details. If you prefer to use automated scripts and avoid human error for setting up the resources for deploying Kubeflow with Cognito, follow this [README](./README-automated.md) instead.

## 1.0 Custom domain and certificates

1. Follow the [Create a subdomain](../add-ons/load-balancer/README.md#create-a-subdomain) section of the load balancer guide to create a subdomain(e.g. `platform.example.com`) for hosting Kubeflow.
1. Follow the [Create certificates for domain](../add-ons/load-balancer/README.md#create-certificates-for-domain) section of the load balancer guide to create certificates required for TLS.

From this point onwards, we will be creating/updating the DNS records **only in the subdomain**. All the screenshots of hosted zone in the following sections/steps of this guide are for the subdomain.
## 2.0 Cognito User Pool

1. Create a user pool in Cognito in the same region as your EKS cluster. Type a pool name and choose `Review defaults`.
1. Email is a required user attribute since Kubeflow uses email address as the user identifier for multi-user isolation. See this [documentation](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation) for example. On the review page, make sure email is selected as a required attribute. If it is not by default, Edit the `Required attributes` and select `email`.
    1. ![cognito-email-required](./images/cognito-email-required.png)
1. On the Policies page, select `Only allow administrators to create users` under `Do you want to allow users to sign themselves up?` and save changes. This step is optional but is recommended to have strict control over the users.
1. Click on `Create pool` to create the user pool.
1. Add an `App client` with any name and the default options.
    1. ![cognito-app-client-id](./images/cognito-app-client-id.png)
1. In the `App client settings`, select `Authorization code grant` flow under OAuth-2.0 and check box `email`, `openid`, `aws.cognito.signin.user.admin` and `profile` scopes. Also check box `Enabled Identity Providers`. 
    1. Substitute `example.com` in this URL - `https://kubeflow.platform.example.com/oauth2/idpresponse` with your domain and use it as the Callback URL(s).
    2. Substitute `example.com` in this URL - `https://kubeflow.platform.example.com` with your domain and use it as the Sign out URL(s).
    3. ![cognito-app-client-settings](./images/cognito-app-client-settings.png)
1. Add a custom domain to the user pool. In order to add a custom domain to your user pool, you need specify a domain name, and provide a certificate managed with AWS Certificate Manager (ACM).
    1. In order to use a custom domain, its root(i.e. `platform.example.com`) must have an valid A type record. Create a new record of type `A` in `platform.example.com` hosted zone with an arbitrary IP for now. Once we have ALB created, we will update this value.
        1. Following is a screenshot of `platform.example.com` hosted zone. A record is shown. 
            1. ![subdomain-initial-A-record](./images/subdomain-initial-A-record.png)
    1. If your cluster is not in N.Virginia(us-east-1), create an ACM certificate in us-east-1 for `*.platform.example.com` by following the process similar to [section 2.0](../add-ons/load-balancer/README.md#create-certificates-for-domain). That is because [Cognito requires](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-pools-add-custom-domain.html) a certificate in N.Virginia in order to have a custom domain for a user pool.
    1. In the `Domain name` choose `Use your domain`, type `auth.platform.example.com` and select the `*.platform.example.com` AWS managed certificate you’ve created in N.Virginia. Creating domain takes up to 15 mins.
        1. ![cognito-active-domain](./images/cognito-active-domain.png)
        2. When it’s created, it will return the `Alias target` CloudFront address.
            1. Screenshot of the CloudFront URL for Cognito Domain name:
                1. ![cognito-domain-cloudfront-url](./images/cognito-domain-cloudfront-url.png)
            2.  Create a new record of type `A` for `auth.platform.example.com` with the value of the CloudFront URL.
                1. Select the `alias` toggle and select Alias to Cloudfront distribution for creating the record
                2. ![cognito-domain-cloudfront-A-record-creating](./images/cognito-domain-cloudfront-A-record-creatin.png)
                3. Following is a screenshot of the A record for `auth.platform.example.com` in `platform.example.com` hosted zone:
                    1. ![cognito-domain-cloudfront-A-record-created](./images/cognito-domain-cloudfront-A-record-created.png)

## 3.0 Configure Ingress

1. Take note of the following values from the previous step or `awsconfigs/infra_configs/scripts/config.yaml` if you used automated guide(./README-automated.md):
    1. The Pool ARN of the user pool found in Cognito general settings.
    1. The App client id, found in Cognito App clients.
    1. The custom user pool domain (e.g. `auth.platform.example.com`), found in the Cognito domain name.
    1. The ARN of the certificate from the Certificate Manager in the region where your platform (for the subdomain) in the region where your platform is running.
    1. signOutURL is the domain which you provided as the Sign out URL(s).
    1. CognitoLogoutURL is comprised of your CognitoUserPoolDomain, CognitoAppClientId, and your domain which you provided as the Sign out URL(s).
    1. Export the values:
        1. 
          ```
          export CognitoUserPoolArn="<YOUR_USER_POOL_ARN>"
          export CognitoAppClientId="<YOUR_APP_CLIENT_ID>"
          export CognitoUserPoolDomain="<YOUR_USER_POOL_DOMAIN>"
          export certArn="<YOUR_ACM_CERTIFICATE_ARN>"
          export signOutURL="<YOUR_SIGN_OUT_URL>"
          export CognitoLogoutURL="https://$CognitoUserPoolDomain/logout?client_id=$CognitoAppClientId&logout_uri=$signOutURL"
          ```
1. Substitute values for setting up Ingress.
    1. ```
        printf '
        CognitoUserPoolArn='$CognitoUserPoolArn'
        CognitoAppClientId='$CognitoAppClientId'
        CognitoUserPoolDomain='$CognitoUserPoolDomain'
        certArn='$certArn'
        ' > awsconfigs/common/istio-ingress/overlays/cognito/params.env
        ```
1. Substitute values for setting up AWS authservice.
    1. ```
        printf '
        LOGOUT_URL='$CognitoLogoutURL'
        ' > awsconfigs/common/aws-authservice/base/params.env
        ```
1. Follow the [Configure Load Balancer Controller](../add-ons/load-balancer/README.md#configure-load-balancer-controller) section of the load balancer guide to setup the resources required the load balancer controller.
## 4.0 Building manifests and deploying Kubeflow

1. Deploy Kubeflow. Choose one of the two options to deploy kubeflow:
    1. **[Option 1]** Install with a single command
        ```
        while ! kustomize build docs/deployment/cognito | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
        ```
    1. **[Option 2]** Install individual components
        ```
        # Kubeflow namespace
        kustomize build common/kubeflow-namespace/base | kubectl apply -f -
        
        # Kubeflow Roles
        kustomize build common/kubeflow-roles/base | kubectl apply -f -
        
        # Istio
        kustomize build common/istio-1-9/istio-crds/base | kubectl apply -f -
        kustomize build common/istio-1-9/istio-namespace/base | kubectl apply -f -
        kustomize build common/istio-1-9/istio-install/base | kubectl apply -f -
        
        # Cert-Manager
        kustomize build common/cert-manager/cert-manager/base | kubectl apply -f -
        kustomize build common/cert-manager/kubeflow-issuer/base | kubectl apply -f -
        
        # KNative
        kustomize build common/knative/knative-serving/overlays/gateways | kubectl apply -f -
        kustomize build common/knative/knative-eventing/base | kubectl apply -f -
        kustomize build common/istio-1-9/cluster-local-gateway/base | kubectl apply -f -
        
        # Kubeflow Istio Resources
        kustomize build common/istio-1-9/kubeflow-istio-resources/base | kubectl apply -f -
        
        # Kubeflow Pipelines
        # reapply manifest if you see an error
        kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user | kubectl apply -f -
        
        # KFServing
        kustomize build apps/kfserving/upstream/overlays/kubeflow | kubectl apply -f -
        
        # Katib
        kustomize build apps/katib/upstream/installs/katib-with-kubeflow | kubectl apply -f -
        
        # Central Dashboard
        kustomize build upstream/apps/centraldashboard/upstream/overlays/istio | kubectl apply -f -
        
        # Notebooks
        kustomize build upstream/apps/jupyter/notebook-controller/upstream/overlays/kubeflow | kubectl apply -f -
        kustomize build awsconfigs/apps/jupyter-web-app | kubectl apply -f -
        
        # Admission Webhook
        kustomize build upstream/apps/admission-webhook/upstream/overlays/cert-manager | kubectl apply -f -
        
        # Profiles + KFAM
        kustomize build upstream/apps/profiles/upstream/overlays/kubeflow | kubectl apply -f -
        
        # Volumes Web App
        kustomize build upstream/apps/volumes-web-app/upstream/overlays/istio | kubectl apply -f -
        
        # Tensorboard
        kustomize build upstream/apps/tensorboard/tensorboards-web-app/upstream/overlays/istio | kubectl apply -f -
        kustomize build upstream/apps/tensorboard/tensorboard-controller/upstream/overlays/kubeflow | kubectl apply -f -
        
        # MPI Operator
        kustomize build upstream/apps/mpi-job/upstream/overlays/kubeflow | kubectl apply -f -

        # Training Operator
        kustomize build upstream/apps/training-operator/upstream/overlays/kubeflow | kubectl apply -f -

        # AWS Telemetry - This is an optional component. See usage tracking documentation for more information
        kustomize build awsconfigs/common/aws-telemetry | kubectl apply -f -

        # Ingress
        kustomize build awsconfigs/common/istio-ingress/overlays/cognito | kubectl apply -f -

        # ALB controller
        kustomize build awsconfigs/common/aws-alb-ingress-controller/base | kubectl apply -f -

        # AWS Authservice
        kustomize build awsconfigs/common/aws-authservice/base | kubectl apply -f -
        ```

## 5.0 Updating the domain with ALB address

1. Check if ALB is provisioned. It takes around 3-5 minutes
    1. ```
        kubectl get ingress -n istio-system
        Warning: extensions/v1beta1 Ingress is deprecated in v1.14+, unavailable in v1.22+; use networking.k8s.io/v1 Ingress
        NAME            CLASS    HOSTS   ADDRESS                                                                  PORTS   AGE
        istio-ingress   <none>   *       ebde55ee-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com   80      15d
        ```
    2. If `ADDRESS` is empty after a few minutes, check the logs of alb-ingress-controller by following [this guide](https://www.kubeflow.org/docs/distributions/aws/troubleshooting-aws/#alb-fails-to-provision)
1. When ALB is ready, copy the DNS name of that load balancer and create a CNAME entry to it in Route53 under subdomain (`platform.example.com`) for `*.platform.example.com`
    1. ![subdomain-*.platform-and-*.default-records](./images/subdomain-*.platform-and-*.default-records.png)
1. Update the type `A` record created in section for `platform.example.com` using ALB DNS name. Change from `127.0.0.1` → ALB DNS name. You have to use alias form under `Alias to application and classical load balancer` and select region and your ALB address.
    1. ![subdomain-A-record-updated](./images/subdomain-A-record-updated.png)
1. Screenshot of all the record sets in hosted zone for reference
    1. ![subdomain-records-summary](./images/subdomain-records-summary.png)

## 6.0 Connecting to Central dashboard

1. The central dashboard should now be available at [https://kubeflow.platform.example.com](https://kubeflow.platform.example.com/). Before connecting to the dashboard:
    1. Head over to the Cognito console and create some users in `Users and groups`. These are the users who will login to the central dashboard.
        1. ![cognito-user-pool-created](./images/cognito-user-pool-created.png)
    1. Create a profile for a user created in previous step by [following this guide](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation). Following is a sample profile for reference:
        1. ```
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
1. Open the central dashboard at [https://kubeflow.platform.example.com](https://kubeflow.platform.example.com/). It will redirect to Cognito for login. Use the credentials of the user for which profile was created in previous step.

