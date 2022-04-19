+++
title = "KServe"
description = "Model serving using KServe with Kubeflow on AWS"
weight = 40
+++

## Model serving over Load Balancer

This tutorial shows how to setup a load balancer endpoint for serving prediction requests over an external DNS on AWS.

### Background

Read the [background](../deployment/add-ons/load-balancer/README.md#background) section of the load balancer guide to familiarize yourself with the requirements for creating an Application Load Balancer on AWS.

### Prerequisites:
1. To keep this guide simple, we will assume you have a Kubeflow deployment with the [AWS Load Balancer controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/) configured because you either have:
    - A Cognito integrated deployment which is configured with [AWS Load Balancer controller by default](../deployment/cognito/README.md#30-configure-ingress) **or**
    - You have followed the [Exposing Kubeflow over Load Balancer guide](../deployment/add-ons/load-balancer/README.md) for non-Cognito based deployment option e.g. [Vanilla](../deployment/vanilla/README.md)(uses Dex as auth provider)
1. Based on the above pre-requisites, you have a subdomain for hosting Kubeflow. For this guide, we will assume you have `platform.example.com` for hosting Kubeflow
1. An existing [profile namespace](https://www.kubeflow.org/docs/components/multi-tenancy/getting-started/#manual-profile-creation) for a user in Kubeflow. For this guide, we will assume you have a profile namespace named `staging`
1. Verify the current directory is the root of the repository by running the `pwd` command. The output should be `<path/to/kubeflow-manifests>` directory


### Configure Knative Serving's domain

KFServing uses Knative Serving for various things like serverless deployment, autoscaling, setting up network routing resources etc. For purpose of this guide, we will focus on the routes. The fully qualified domain name(FQDN) for a route in Knative Serving by default is `{route}.{namespace}.{default-domain}`. Knative Serving routes use `example.com` as the default domain ([Reference](https://knative.dev/docs/serving/using-a-custom-domain/#default-domain-name-settings)). For example, if you create an `InferenceService` resource called `sklearn-iris` in `staging` namespace. Its URL would be `http://sklearn-iris.staging.example.com`. This is also the default configuration in Knative Serving component deployed as part of your Kubeflow deployment. You will need to configure the default domain as per your deployment. Let's see how:

As you understand from the [background](#background) section, we need to use a custom domain to configure HTTPS with load balancer. We recommend using HTTPS to to enable traffic encryption between the clients and your load balancer. So, if you are using `platform.example.com` domain to host Kubeflow, you will need to edit the `config-domain` ConfigMap in the `knative-serving` namespace to configure the `platform.example.com` to be used as the domain for the routes.

**Follow the instructions** in the [procedure section of the using a custom domain guide](https://knative.dev/docs/serving/using-a-custom-domain/#procedure) on the Knative Serving documentation to configure the default domain used by Knative. You would remove the `_example` key and replace `example.com` with your domain e.g. `platform.example.com`. Following is a sample:

```
apiVersion: v1
kind: ConfigMap
data:
  platform.example.com: ""
...
```

### Create a certificate to use with Load Balancer

To get TLS support from the ALB, you need to request a certificate in AWS Certificate Manager. Since Knative concatenates the namespace in the FQDN for a route and it is delimited by a dot by default, the URLs for `InferenceServices` created in each namespace will be in a different [subdomain](https://en.wikipedia.org/wiki/Subdomain). For example, if you have 2 namespaces, `staging` and `prod` and create an `InferenceService` resource called `sklearn-iris` in both the namespaces, the URLs for each resource will be `http://sklearn-iris.staging.platform.example.com` and `http://sklearn-iris.prod.platform.example.com` respectively. This means, you will need to specify all the subdomains in which you plan to create InferenceService while creating the SSL certificate in ACM. For example, in the case with staging and prod namespaces, you will need to add `*.prod.platform.example.com`, `*.staging.platform.example.com` and `*.platform.example.com` to the certificate. This is because DNS only supports wildcard in the [leftmost part of the domain name](https://en.wikipedia.org/wiki/Wildcard_DNS_record) e.g. `*.platform.example.com`. When you request a wild-card certificate, the asterisk (*) must be in the leftmost position of the domain name and can protect only one subdomain level. For example, `*.platform.example.com` can protect `staging.platform.example.com`, and `prod.platform.example.com`, but it cannot protect `sklearn-iris.staging.platform.example.com`.

For this tutorial, create an ACM certificate for `*.platform.example.com` and `*.staging.platform.example.com`(**both domains in the same certificate**) in the region where your cluster exists by following the process similar to [create certificates for domain](../deployment/add-ons/load-balancer/README.md#create-certificates-for-domain) section of the load balancer guide. Once the certificate status changes to `Issued`, export the ARN of the certificate created:
1. `export certArn=<>` 

If you use Dex as auth provider in your Kubeflow deployment, refer the [Dex specific section](#dex---update-the-load-balancer). If you use Cognito, continue to the next section

### Cognito - Create a HTTP header evaluation based Load Balancer

Currently, it is not possible to programatically authenticate a request through ALB that is using Amazon Cognito to authenticate users. (i.e. you cannot generate the `AWSELBAuthSessionCookie` cookies by using the access tokens from Cognito). We will be creating a new Application Load Balancer(ALB) endpoint for serving traffic which authorizes based on custom strings specified in a predefined HTTP header. We will use an ingress to set [HTTP header conditions](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html#http-header-conditions) on ALB which will configure rules that route requests based on the HTTP headers in the request. This can be used for service to service communication in your application.

#### Create Ingress

1. Configure the following parameters for [ingress](../../awsconfigs/common/istio-ingress/overlays/api/params.env). `httpHeaderName` and `httpHeaderValues` correspond to HttpHeaderName and Values from [HttpHeaderConfig](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-listeners.html#http-header-conditions)
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

### Dex - Update the Load Balancer

#### Update the certificate for ALB

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

### Add DNS records for the staging subdomain with ALB address

When ALB is ready/updated, copy the ADDRESS of that load balancer and create a CNAME entry to it in Route53 under subdomain (`platform.example.com`) for `*.staging.platform.example.com`

### Run a sample InferenceService

1. [Known Issue] Namespaces created by Kubeflow profile controller have a missing authorization policy which prevent the KFServing predictor and transformer to work([kserve/kserve#1558](https://github.com/kserve/kserve/issues/1558), [kubeflow/kubeflow#5965](https://github.com/kubeflow/kubeflow/issues/5965)). You will need to create the `AuthorizationPolicy` as mentioned in [#82 (comment)](https://github.com/awslabs/kubeflow-manifests/issues/82#issuecomment-1068641378) as a workaround until this is resolved. Verify the policies have been created by listing the `authorizationpolicies` in the `istio-system` namespace:
    1. ```
        kubectl get authorizationpolicies -n istio-system
        ```
1. Create a sample sklearn InferenceService using a [sample](https://github.com/kubeflow/kfserving-lts/blob/release-0.6/docs/samples/v1beta1/sklearn/v1/sklearn.yaml) from the KFserving repository and wait for it to be `READY`
    1. ```
        kubectl apply -n staging -f https://raw.githubusercontent.com/kubeflow/kfserving-lts/release-0.6/docs/samples/v1beta1/sklearn/v1/sklearn.yaml
        ```
1. Check `InferenceService` status. Once it is `READY`, get the URL and use it for sending prediction request
    ```
    kubectl get inferenceservices sklearn-iris -n staging

    NAME           URL                                                READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                    AGE
    sklearn-iris   http://sklearn-iris.staging.platform.example.com   True           100                              sklearn-iris-predictor-default-00001   3m31s
    ```
1. Send an inference request:
    - Export the values for `KUBEFLOW_DOMAIN`(e.g. `platform.example.com`) and `PROFILE_NAMESPACE`(e.g. `staging`) according to your environment:
        1. ```
            export KUBEFLOW_DOMAIN="platform.example.com"
            export PROFILE_NAMESPACE="staging"
            ```
    - Install dependencies for the script by running `pip install requests`
    - Run the sample python script to send an inference request based on your auth provider:
        - **[Cognito]** Run the [inference_sample_cognito.py](../../tests/e2e/utils/kserve/inference_sample_cognito.py) Python script by exporting the values for `HTTP_HEADER_NAME`(e.g. `x-api-key`) and `HTTP_HEADER_VALUE`(e.g. `token1`) according to the values configured in [ingress section](#create-ingress)
            1. ```
               export HTTP_HEADER_NAME="x-api-key"
               export HTTP_HEADER_VALUE="token1"

               python tests/e2e/utils/kserve/inference_sample_cognito.py
               ```

                Output would look like:
                ```
                Status Code 200
                JSON Response  {'predictions': [1, 1]}
                ```
        - **[Dex]** Run the [inference_sample_dex.py](../../tests/e2e/utils/kserve/inference_sample_dex.py) Python script by exporting the values for `USERNAME`(e.g. `user@example.com`), `PASSWORD` according to the user profile 
            1. ```
               export USERNAME="user@example.com"
               export PASSWORD="12341234"

               python tests/e2e/utils/kserve/inference_sample_dex.py
               ```

                Output would look like:
                ```
                Status Code 200
                JSON Response  {'predictions': [1, 1]}
                ```
