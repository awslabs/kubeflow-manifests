+++
title = "Pipelines"
description = "Get started with Kubeflow Pipelines on Amazon EKS"
weight = 20
+++

For an overview of connecting to Kubeflow Pipelines using the SDK client, see [the Pipelines SDK guide](https://www.kubeflow.org/docs/components/pipelines/sdk/connect-api/).

## Authenticate Kubeflow Pipelines using SDK inside cluster

Refer to the following guide to connect to Kubeflow Pipelines from [inside your cluster](https://www.kubeflow.org/docs/components/pipelines/sdk/connect-api/#connect-to-kubeflow-pipelines-from-the-same-cluster).

## Authenticate Kubeflow Pipelines using SDK outside cluster

Refer to the following guide to connect to Kubeflow Pipelines from [outside your cluster](https://www.kubeflow.org/docs/components/pipelines/sdk/connect-api/#connect-to-kubeflow-pipelines-from-outside-your-cluster).

Refer to the following steps to use `kfp` to pass a cookie from your browser after you log into Kubeflow. The following example uses a Chrome browser.

![](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/pipelines/kfp-sdk-browser-cookie.png)

![](https://raw.githubusercontent.com/awslabs/kubeflow-manifests/main/website/content/en/docs/images/pipelines/kfp-sdk-browser-cookie-detail.png)

Once you get a cookie, authenticate `kfp` by passing the cookie from your browser. Use the session based on the appropriate manifest for your deployment, as done in the following examples.

### **Dex**

If you want to use port forwarding to access Kubeflow, run the following command and use `http://localhost:8080/pipeline` as the host.

```bash
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

Pass the cookie from your browser:

```bash
# This is the "Domain" in your cookies. Eg: "localhost:8080" or "<ingress_alb_address>.elb.amazonaws.com"
kubeflow_gateway_endpoint="<YOUR_KUBEFLOW_GATEWAY_ENDPOINT>"

authservice_session_cookie="<YOUR_COOKIE>"

namespace="<YOUR_NAMESPACE>"

client = kfp.Client(host=f"http://{kubeflow_gateway_endpoint}/pipeline", cookies=f"authservice_session={authservice_session_cookie}")
client.list_experiments(namespace=namespace)
```

If you want to set up application load balancing (ALB) with Dex, see the [Load Balancer](/kubeflow-manifests/deployments/add-ons/load-balancer/guide/) and use the ALB address as the Kubeflow Endpoint.

To do programmatic authentication with Dex, refer to the following comments under [issue #140](https://github.com/kubeflow/kfctl/issues/140) in the `kfctl` repository: [#140 (comment)](https://github.com/kubeflow/kfctl/issues/140#issuecomment-578837304) and [#140 (comment)](https://github.com/kubeflow/kfctl/issues/140#issuecomment-719894529).

### **Cognito**

```bash
# This is the "Domain" in your cookies. eg: kubeflow.<platform.example.com>
kubeflow_gateway_endpoint="<YOUR_KUBEFLOW_HTTPS_GATEWAY_ENDPOINT>"

alb_session_cookie0="<YOUR_COOKIE_0>"
alb_session_cookie1="<YOUR_COOKIE_1>"

namespace="<YOUR_NAMESPACE>"

client = kfp.Client(host=f"https://{kubeflow_gateway_endpoint}/pipeline", cookies=f"AWSELBAuthSessionCookie-0={alb_session_cookie0};AWSELBAuthSessionCookie-1={alb_session_cookie1}")
client.list_experiments(namespace=namespace)
```

## AWS Access from Pipeline Components

For pipelines component to be granted access to AWS resources, the corresponding profile in which the pipeline is created needs to be configured with the `AwsIamForServiceAccount` plugin.

Below is an example of a profile using the `AwsIamForServiceAccount` plugin:
```yaml
apiVersion: kubeflow.org/v1
kind: Profile
metadata:
  name: some_profile
spec:
  owner:
    kind: User
    name: some-user@kubeflow.org
  plugins:
  - kind: AwsIamForServiceAccount
    spec:
      awsIamRole: arn:aws:iam::123456789012:role/some-profile-role
```

The AWS IAM permissions granted to the pipelines components are specified in the profile's `awsIamRole`. 

To configure the `AwsIamForServiceAccount` plugin to work with profiles, follow the [Configuration Steps](#configuration-steps) below.

### Configuration steps

Configuration steps to configure profiles with AWS IAM permissions can be found [here](./profiles.md#configuration-steps).
The configuration steps will configure the profile controller to work with the `AwsIamForServiceAccount` plugin.

### Example: S3 Access from a Pipeline Component

The below steps walk through creating a pipeline with a component that has permissions to list buckets in S3.
#### Prerequisites
1. [Vanilla kubeflow installation](/kubeflow-manifests/docs/deployment/vanilla)
2. Completed [configuration steps](#configuration-steps)

#### Steps

1. Port forward the central dashboard.

   ```bash
   kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
   ```

2. A script will created that will create the pipeline. Install the script dependencies. The script requires python 3.6 or greater. (opitonal: You can run this code from notebook too, after logging in to the central dashboard).

   ```bash
   pip install boto3 kfp requests
   ```

3. Copy the below script to a file.

   Replace `DEFAULT_USER_NAMESPACE` with the `PROFILE_NAME` for the profile created in step 9 of the [configuration steps](#configuration-steps).

   ```python
   import kfp
   import requests

   DEFAULT_HOST = "http://localhost:8080/"
   DEFAULT_USER_NAMESPACE = <replace me>
   DEFAULT_USERNAME = "user@example.com"
   DEFAULT_PASSWORD = "12341234"
   KUBEFLOW_NAMESPACE = "kubeflow"

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

   def kfp_client(host, client_namespace, session_cookie):

       client = kfp.Client(
           host=f"{host}/pipeline",
           cookies=f"authservice_session={session_cookie}",
           namespace=client_namespace,
       )
       client._context_setting[
           "namespace"
       ] = client_namespace  # needs to be set for list_experiments

       return client

   def s3_op():
       import boto3
       s3 = boto3.client("s3", region_name="us-west-2")
       resp = s3.list_buckets()
       print(resp)

   s3_op = kfp.components.create_component_from_func(
       s3_op, base_image="python", packages_to_install=["boto3"]
   )

   def s3_pipeline():
       s3_operation = s3_op()

   sc = session_cookie(DEFAULT_HOST, DEFAULT_USERNAME, DEFAULT_PASSWORD)
   client = kfp_client(DEFAULT_HOST, DEFAULT_USER_NAMESPACE, sc)
   client.create_run_from_pipeline_func(
       s3_pipeline, namespace=DEFAULT_USER_NAMESPACE, arguments={}
   )
   ```

4. Run the created script file.

   ```bash
   python <script_file>.py
   ```

5. Login to the central dashboard.

   1. Open your browser and visit `http://localhost:8080`. You should get the Dex login screen.
   2. Login with the default user's credential. The default email address is `user@example.com` and the default password is `12341234`.

6. Navigate to the runs dasbhoard and view the `s3_op` component in the graph. In the logs sections the buckets in the s3 account should be viewable.

## Support S3 as a source for Kubeflow Pipelines output viewers

Support for S3 Artifact Store is in active development. You can track the [open issue](https://github.com/awslabs/kubeflow-manifests/issues/117) to stay up-to-date on progress.

## Support TensorBoard in Kubeflow Pipelines

Support for TensorBoard in Kubeflow Pipelines is in active development. You can track the [open issue](https://github.com/awslabs/kubeflow-manifests/issues/118) to stay up-to-date on progress.
