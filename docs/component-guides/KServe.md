## Model serving over Load Balancer using KFServing

This tutorial shows how to setup a load balancer endpoint for serving prediction requests over an external DNS on AWS.

## Background

Read the [background](../deployment/add-ons/load-balancer/README.md#background) section of the load balancer guide to familiarize yourself with the requirements for creating an Application Load Balancer on AWS.

## Prerequisites:
1. To keep this guide simple, we will assume you have a Kubeflow deployment with the [AWS Load Balancer controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) configured because you either have:
    - A Cognito integrated deployment which is configured with [AWS Load Balancer controller by default](../deployment/cognito/README.md#30-configure-ingress) **or**
    - You have followed the [Exposing Kubeflow over Load Balancer guide](../deployment/add-ons/load-balancer/README.md) for non-Cognito based deployment option e.g. [Vanilla](../deployment/vanilla/README.md)(uses Dex as auth provider)
1. Based on the above pre-requisites, you have a subdomain for hosting Kubeflow. For this guide, we will assume you have `platform.example.com` for hosting Kubeflow
1. An existing [profile namespace](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation) for a user in Kubeflow. For this guide, we will assume you have a profile namespace named `staging`
1. Verify the current directory is the root of the repository by running the `pwd` command. The output should be `<path/to/kubeflow-manifests>` directory


## Customize Knative Serving domain

KFServing uses Knative Serving for various things like serverless deployment, autoscaling, setting up network routing resources etc. For purpose of this guide, we will focus on the routes. The fully qualified domain name(FQDN) for a route in Knative Serving by default is `{route}.{namespace}.{default-domain}`. Knative Serving routes use `example.com` as the default domain ([Reference](https://knative.dev/docs/serving/using-a-custom-domain/#default-domain-name-settings)). For example, if you create an `InferenceService` resource called `sklearn-iris` in `serving` namespace. Its URL would be `http://sklearn-iris.staging.example.com`. This is also the default configuration in Knative Serving component deployed as part of your Kubeflow deployment. You will need to configure the default domain as per your deployment. Let's see how:

As you understand from the [background](#background) section, we need to use a custom domain to configure HTTPS with load balancer. We recommend using HTTPS to to enable traffic encryption between the clients and your load balancer. So, if you are using `platform.example.com` domain to host Kubeflow, you will need to edit the `config-domain` ConfigMap in the `knative-serving` namespace to configure the `platform.example.com` to be used as the domain for the routes.  Follow the instructions in the [procedure](https://knative.dev/docs/serving/using-a-custom-domain/#procedure) section of Knative Serving documentation to configure the default domain used by Knative.

## Create a certificate to use with Load Balancer

To get TLS support from the ALB, you need to request a certificate in AWS Certificate Manager. Since Knative concatenates the namespace in the FQDN for a route and it is delimited by a dot by default, the URLs for `InferenceServices` created in each namespace will be in a different [subdomain](https://en.wikipedia.org/wiki/Subdomain). For example, if you have 2 namespaces, `staging` and `prod` and create an `InferenceService` resource called `sklearn-iris` in both the namespaces, the URLs for each resource will be `http://sklearn-iris.staging.platform.example.com` and `http://sklearn-iris.prod.platform.example.com` respectively. This means, you will need to specify all the subdomains in which you plan to create InferenceService while creating the SSL certificate in ACM. For example, in the case with staging and prod namespaces, you will need to add `*.prod.platform.example.com`, `*.staging.platform.example.com` and `*.platform.example.com` to the certificate. This is because DNS only supports wildcard in the [leftmost part of the domain name](https://en.wikipedia.org/wiki/Wildcard_DNS_record) e.g. `*.platform.example.com`. When you request a wild-card certificate, the asterisk (*) must be in the leftmost position of the domain name and can protect only one subdomain level. For example, `*.platform.example.com` can protect `staging.platform.example.com`, and `prod.platform.example.com`, but it cannot protect `sklearn-iris.staging.platform.example.com`.

For this tutorial, create a certificate by following [this ACM document](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html#request-public-console) for `*.platform.example.com` and `*.staging.platform.example.com`(both domains in the same certificate) in the region where your cluster exists. Certificate is only valid upon [validation of domain ownership](https://docs.aws.amazon.com/acm/latest/userguide/domain-ownership-validation.html). After successful validation, the certificate status will be `Issued`. Export the ARN of the certificate created:
1. `export certArn=<>` 

If you use Dex as auth provider in your Kubeflow deployment, refer the [Dex specific section](#dex---update-the-load-balancer). If you use Cognito, continue to the next section

## Cognito - Create a HTTP header evaluation based Load Balancer

Currently, it is not possible to programatically authenticate a request through ALB that is using Amazon Cognito to authenticate users. (i.e. you cannot generate the `AWSELBAuthSessionCookie` cookies by using the access tokens from Cognito). Instead of using the existing ALB, we will be creating another Application Load Balancer(ALB) endpoint which authorizes based on custom strings specified in a predefined HTTP header. We will use an ingress to set [HTTP header conditions](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html#http-header-conditions) on ALB which will configure rules that route requests based on the HTTP headers in the request. This can be used for service to service communication in your application.

### Create Ingress

1. Configure the following parameters for [ingress](../../awsconfigs/common/istio-ingress/overlays/api/params.env):
    - certArn: ARN of certificate created in previous step
    - (optional) httpHeaderName: Custom HTTP header name you want to configure for the rule evaluation. Default is `x-api-key`
    - httpHeaderValues: one or more match strings that need to be compared against the header value in the request received. You only need to pass one of the tokens in the request. Pick strong values.
    1. Replace the `token1` string with a token of your choice and optionally the httpHeaderName
        ```
        printf '
        certArn='$certArn'
        httpHeaderName=x-api-key
        httpHeaderValues=["token1"]
        ' > awsconfigs/common/istio-ingress/overlays/api/params.env
        ```
1. Create the ingress by running the following command:
    1. ```
       kustomize build awsconfigs/common/istio-ingress/overlays/api | kubectl apply -f -
       ```
1. Check if the ingress managed ALB is provisioned. It takes around 3-5 minutes
    1. ```
        kubectl get ingress -n istio-system istio-ingress-api
        NAME                CLASS    HOSTS   ADDRESS                                                                PORTS   AGE
        istio-ingress-api   <none>   *       xxxxxx-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com   80      14m
        ```
1. Once ALB is ready, you will need to add a DNS record for the staging subdomain. [Add DNS records for the staging subdomain with ALB address](#add-dns-records-for-the-staging-subdomain-with-alb-address) section will guide you through it

## Dex - Update the Load Balancer

### Update the certificate for ALB

1. Configure the parameters for [ingress](../../../../awsconfigs/common/istio-ingress/overlays/https/params.env) with the new certificate ARN created in previous section
    1. ```
        printf 'certArn='$certArn'' > awsconfigs/common/istio-ingress/overlays/https/params.env
        ```
1. Update the ALB:
    1. ```
        kustomize build awsconfigs/common/istio-ingress/overlays/https | kubectl apply -f -
        ``` 
1. Get the ALB Address
    1. ```
        kubectl get ingress -n istio-system istio-ingress
        NAME            CLASS    HOSTS   ADDRESS                                                                  PORTS   AGE
        istio-ingress   <none>   *       xxxxxx-istiosystem-istio-2af2-1100502020.us-west-2.elb.amazonaws.com   80      15d
        ```

## Add DNS records for the staging subdomain with ALB address

When ALB is ready/updated, copy the ADDRESS of that load balancer and create a CNAME entry to it in Route53 under subdomain (`platform.example.com`) for `*.staging.platform.example.com`

## Run a sample InferenceService

1. [Known Issue] Namespaces created by Kubeflow profile controller have a missing authorization policy which prevent the KFServing predictor and transformer to work. See the following related issues: [kserve/kserve#1558](https://github.com/kserve/kserve/issues/1558), [kubeflow/kubeflow#5965](https://github.com/kubeflow/kubeflow/issues/5965) for more information. You will need to apply the `AuthorizationPolicy` as mentioned in [#82 (comment)](https://github.com/awslabs/kubeflow-manifests/issues/82#issuecomment-1068641378) as a workaround until this is resolved
1. Create a sample sklearn InferenceService using a [sample](https://github.com/kubeflow/kfserving-lts/blob/release-0.6/docs/samples/v1beta1/sklearn/v1/sklearn.yaml) from the KFserving repository and wait for it to be READY
    1. ```
        kubectl apply -n staging -f https://raw.githubusercontent.com/kubeflow/kfserving-lts/release-0.6/docs/samples/v1beta1/sklearn/v1/sklearn.yaml
        ```
1. Check `InferenceService` status. Once it is `Ready`, get the URL and use it for sending prediction request
    ```
    kubectl get inferenceservices sklearn-iris -n staging

    NAME           URL                                                READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                    AGE
    sklearn-iris   http://sklearn-iris.staging.platform.example.com   True           100                              sklearn-iris-predictor-default-00001   3m31s
    ```
1. Send an inference request using the sample python script below based on your auth provider:
    - **[Cognito]** Run the following Python script by substituting the values for `URL`, `Host` according to your environment and custom HTTP header name(e.g. `x-api-key`) and value(e.g. `token1`) according to the values configured in [ingress section](#create-ingress)
        1. ```
            import requests

            KUBEFLOW_DOMAIN = "platform.example.com"
            PROFILE_NAMESPACE = "staging"
            URL = f"https://sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v1/models/sklearn-iris:predict"
            HEADERS = {
              "Host" : f"sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}",
              "x-api-key": "token1"
            }

            data = {
                "instances": [
                    [6.8,  2.8,  4.8,  1.4],
                    [6.0,  3.4,  4.5,  1.6]
                ]
            }


            response = requests.post(URL, headers=HEADERS, json=data)
            print("Status Code", response.status_code)
            print("JSON Response ", response.json())
            ```
            
            Output would look like:
            ```
            python inference_sample.py

            Status Code 200
            JSON Response  {'predictions': [1, 1]}
            ```
    - **[Dex]** Run the following Python script by substituting the values for `KUBEFLOW_DOMAIN`, `PROFILE_NAMESPACE`, `USERNAME` and `PASSWORD` according to your environment 
        1. ```
            import requests

            KUBEFLOW_DOMAIN = "platform.example.com"
            PROFILE_NAMESPACE = "staging"
            USERNAME = "user@example.com"
            PASSWORD = "12341234"

            URL = f"https://sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v1/models/sklearn-iris:predict"
            HEADERS = {
              "Host" : f"sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}"
            }
            DASHBOARD_URL = f"https://kubeflow.{KUBEFLOW_DOMAIN}"

            data = {
                "instances": [
                    [6.8,  2.8,  4.8,  1.4],
                    [6.0,  3.4,  4.5,  1.6]
                ]
            }

            def session_cookie(host, login, password):
                session = requests.Session()
                response = session.get(host)
                headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                }
                data = {"login": login, "password": password}
                session.post(response.url, headers=headers, data=data)
                session_cookie = session.cookies.get_dict()["authservice_session"]
                return session_cookie

            cookie = {
                "authservice_session" : session_cookie(DASHBOARD_URL, USERNAME, PASSWORD)
            }

            response = requests.post(URL, headers=HEADERS, json=data, cookies=cookie)
            print("Status Code", response.status_code)
            print("JSON Response ", response.json())
            ```

            Output would look like:
            ```
            python inference_sample.py

            Status Code 200
            JSON Response  {'predictions': [1, 1]}
            ```
