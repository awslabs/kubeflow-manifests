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

If you want to set up application load balancing (ALB) with Dex, see the [Load Balancer](/kubeflow-manifests/docs/deployment/add-ons/load-balancer/guide/) and use the ALB address as the Kubeflow Endpoint.

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

## AWS Access from Kubeflow Pipelines

User profiles can be granted permissions to access AWS resources. Pipelines under the profile namespace will have access to AWS resources as specified in the user profile's `awsIamRole`.

## Configuration steps

Generic configuration steps to configure user profiles with AWS IAM permissions can be found [here](./profiles.md#configuration-steps).

The below configuration steps provide an end to end example of configuring user profiles with IAM permissions and using them with the KFP SDK.

### Prerequisites

Deploy Kubeflow using the [vanilla](/kubeflow-manifests/docs/deployment/vanilla) deployment option.

### Create the profile

1. Define the following environment variables:

   ```bash
   export CLUSTER_NAME=<your cluster name>
   export CLUSTER_REGION=<your region>
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
   export PROFILE_NAME=<the name of the profile to be created>
   ```

2. Create an IAM policy using the [IAM Profile controller policy](https://github.com/awslabs/kubeflow-manifests/blob/main/awsconfigs/infra_configs/iam_profile_controller_policy.json) file.

   ```bash
   aws iam create-policy \
   --region $CLUSTER_REGION \
   --policy-name kf-profile-controller-policy \
   --policy-document file://awsconfigs/infra_configs/iam_profile_controller_policy.json
   ```

3. Associate IAM OIDC with your cluster.

   ```bash
   aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

   eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --region $CLUSTER_REGION --approve
   ```

4. Create an IRSA for the Profile controller using the policy.

   ```bash
   eksctl create iamserviceaccount \
   --cluster=$CLUSTER_NAME \
   --name="profiles-controller-service-account" \
   --namespace=kubeflow \
   --attach-policy-arn="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/kf-profile-controller-policy" \
   --region=$CLUSTER_REGION \
   --override-existing-serviceaccounts \
   --approve
   ```

5. Create an IAM trust policy to authorize federated requests from the OIDC provider.

   ```bash
   export OIDC_URL=$(aws eks describe-cluster --region $CLUSTER_REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)

   cat <<EOF > trust.json
   {
   "Version": "2012-10-17",
   "Statement": [
       {
       "Effect": "Allow",
       "Principal": {
           "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${OIDC_URL}"
       },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
           "StringEquals": {
           "${OIDC_URL}:aud": "sts.amazonaws.com"
           }
       }
       }
   ]
   }
   EOF
   ```

6. [Create an IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html) to scope the permissions for the Profile. For simplicity, we will use the `arn:aws:iam::aws:policy/AmazonS3FullAccess` policy as an example.

7. [Create an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html) for the Profile using the scoped policy from the previous step.

   ```bash
   aws iam create-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

   aws iam attach-role-policy --role-name $PROFILE_NAME-$CLUSTER_NAME-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
   ```

8. Create a Profile using the `PROFILE_NAME`.

   ```bash
   cat <<EOF > profile_iam.yaml
   apiVersion: kubeflow.org/v1
   kind: Profile
   metadata:
     name: ${PROFILE_NAME}
   spec:
     owner:
       kind: User
       name: user@example.com
     plugins:
     - kind: AwsIamForServiceAccount
       spec:
         awsIamRole: $(aws iam get-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --output text --query 'Role.Arn')
   EOF

   kubectl apply -f profile_iam.yaml
   ```

## Verification steps

These steps continue from the configuration steps above but can be used as a starting point for other configurations.

1. Port forward the central dashboard.

   ```
   kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
   ```

2. Install the verification script dependencies. The script requires python 3.6 or greater.

   ```
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

   ```
   python <script_file>.py
   ```

5. Login to the central dashboard.

   1. Open your browser and visit `http://localhost:8080`. You should get the Dex login screen.
   2. Login with the default user's credential. The default email address is `user@example.com` and the default password is `12341234`.

6. Navigate to the runs dasbhoard and view the `s3_op` component in the graph. In the logs sections the buckets in the s3 account should be viewable.

7. Create an IRSA for the Profile controller using the policy.

   ```bash
   eksctl create iamserviceaccount \
   --cluster=$CLUSTER_NAME \
   --name="profiles-controller-service-account" \
   --namespace=kubeflow \
   --attach-policy-arn="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/kf-profile-controller-policy" \
   --region=$CLUSTER_REGION \
   --override-existing-serviceaccounts \
   --approve
   ```

8. Create an IAM trust policy to authorize federated requests from the OIDC provider.

   ```bash
   export OIDC_URL=$(aws eks describe-cluster --region $CLUSTER_REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)

   cat <<EOF > trust.json
   {
   "Version": "2012-10-17",
   "Statement": [
       {
       "Effect": "Allow",
       "Principal": {
           "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${OIDC_URL}"
       },
       "Action": "sts:AssumeRoleWithWebIdentity",
       "Condition": {
           "StringEquals": {
           "${OIDC_URL}:aud": "sts.amazonaws.com"
           }
       }
       }
   ]
   }
   EOF
   ```

9. [Create an IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html) to scope the permissions for the Profile. For simplicity, we will use the `arn:aws:iam::aws:policy/AmazonS3FullAccess` policy as an example.

10. [Create an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html) for the Profile using the scoped policy from the previous step.

    ```bash
    aws iam create-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

    aws iam attach-role-policy --role-name $PROFILE_NAME-$CLUSTER_NAME-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    ```

11. Create a Profile using the `PROFILE_NAME`.

    ```bash
    cat <<EOF > profile_iam.yaml
    apiVersion: kubeflow.org/v1
    kind: Profile
    metadata:
      name: ${PROFILE_NAME}
    spec:
      owner:
        kind: User
        name: user@example.com
      plugins:
      - kind: AwsIamForServiceAccount
        spec:
          awsIamRole: $(aws iam get-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --output text --query 'Role.Arn')
    EOF

    kubectl apply -f profile_iam.yaml
    ```

## Verification steps

These steps continue from the configuration steps above but can be used as a starting point for other configurations.

1. Port forward the central dashboard.

   ```
   kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
   ```

2. Install the verification script dependencies. The script requires python 3.6 or greater.

   ```
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

   ```
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
