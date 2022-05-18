+++
title = "Katib"
description = "Get started with Katib on Amazon EKS"
weight = 20
+++

## AWS Access from Katib

User profiles can be granted permissions to access AWS resources. Katib experiments under the profile namespace will have access to AWS resources as specified in the user profile's `awsIamRole`.

More background on user profiles with AWS IAM permissions can be found [here](./profiles.md#iam-roles-for-service-accounts).

As a summary of the linked background, the `AwsIamForServiceAccount` plugin in the `profiles-controller` is responsible for configuring the `default-editor` service account (SA) to be an IAM role service account (IRSA). The `default-editor` IRSA is annotated with the profile's role which defines the IAM permissions pods belonging to the `default-editor` will have.

Katib experiments belong to the `default` service account in the profile's namespace so the configuration steps below will not use the `AwsIamForServiceAccount` plugin in the `profiles-controller`. This is because the plugin is only able to configure the `default-editor` SA as an IRSA. The steps below will configure the `default` SA as an IRSA so that Katib experiment pods and job pods will have permissions to access AWS services as scoped by the IRSA policy.

## Configuration steps

After installing Kubeflow on AWS with one of the available [deployment options](/kubeflow-manifests/docs/deployment/), you can configure Kubeflow Profiles with the following steps:

1. Define the following environment variables:

   ```bash
   export CLUSTER_NAME=<your cluster name>
   export CLUSTER_REGION=<your region>
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
   export PROFILE_NAME=<the name of the profile to be created>
   ```

2. Associate IAM OIDC with your cluster.

   ```bash
   aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

   eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --region $CLUSTER_REGION --approve
   ```

3. Create a user in your configured auth provider (e.g. Cognito or Dex) or use an existing user.

   Export the user as an environment variable. For simplicity, we will use the `user@example.com` user that is created by default by most of our provided deployment options.

   ```bash
   export PROFILE_USER="user@example.com"
   ```

4. Create a Profile using the `PROFILE_NAME`.

   ```bash
   cat <<EOF > profile_iam.yaml
   apiVersion: kubeflow.org/v1
   kind: Profile
   metadata:
     name: ${PROFILE_NAME}
   spec:
     owner:
       kind: User
       name: ${PROFILE_USER}
   EOF

   kubectl apply -f profile_iam.yaml
   ```

5. Create an IAM trust policy to authorize federated requests from the OIDC provider and allow the SA to assume the role permissions.

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
           "${OIDC_URL}:aud": "sts.amazonaws.com",
           "${OIDC_URL}:sub": ["system:serviceaccount:${PROFILE_NAME}:default-editor"]
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

8. Make the `default` SA an IRSA using the create IAM role.

   ```bash
   eksctl create iamserviceaccount \
   --cluster=$CLUSTER_NAME \
   --name=default \
   --namespace=${PROFILE_NAME} \
   --attach-role-arn=$(aws iam get-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --query "Role.Arn" --output text) \
   --region=$CLUSTER_REGION \
   --override-existing-serviceaccounts \
   --approve
   ```

## Verification steps

9. Create the following Katib experiment yaml:

   ```bash
   cat <<EOF > experiment.yaml

   apiVersion: kubeflow.org/v1beta1
   kind: Experiment
   metadata:
     namespace: ${PROFILE_NAME}
     name: test
   spec:
     objective:
       type: maximize
       goal: 0.90
       objectiveMetricName: Validation-accuracy
       additionalMetricNames:
         - Train-accuracy
     algorithm:
       algorithmName: random
     parallelTrialCount: 3
     maxTrialCount: 12
     maxFailedTrialCount: 1
     parameters:
       - name: lr
         parameterType: double
         feasibleSpace:
           min: "0.01"
           max: "0.03"
       - name: num-layers
         parameterType: int
         feasibleSpace:
           min: "2"
           max: "5"
       - name: optimizer
         parameterType: categorical
         feasibleSpace:
           list:
             - sgd
             - adam
             - ftrl
     trialTemplate:
       primaryContainerName: training-container
       trialParameters:
         - name: learningRate
           description: Learning rate for the training model
           reference: lr
         - name: numberLayers
           description: Number of training model layers
           reference: num-layers
         - name: optimizer
           description: Training model optimizer (sdg, adam or ftrl)
           reference: optimizer
       trialSpec:
         apiVersion: batch/v1
         kind: Job
         spec:
           template:
             metadata:
               annotations:
                 sidecar.istio.io/inject: "false"
             spec:
               containers:
                 - name: training-container
                   image: public.ecr.aws/z1j2m4o4/kubeflow-katib-mxnet-mnist:latest
                   command:
                     - "python3"
                     - "/opt/mxnet-mnist/list_s3_buckets.py"
                     - "&&"
                     - "python3"
                     - "/opt/mxnet-mnist/mnist.py"
                     - "--batch-size=64"
                     - "--lr=${trialParameters.learningRate}"
                     - "--num-layers=${trialParameters.numberLayers}"
                     - "--optimizer=${trialParameters.optimizer}"
               restartPolicy: Never
   EOF
   ```

10. Create the experiment.

    ```bash
    kubectl apply -f experiment.yaml
    ```

11. Describe the experiment.

    ```bash
    kubectl describe experiments -n ${PROFILE_NAME} test
    ```

    After around 5 minutes the status should be successfull.
