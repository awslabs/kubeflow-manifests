+++
title = "Create Profiles with IAM role"
description = "Use AWS IAM roles for service accounts with Kubeflow Profiles"
weight = 70
+++

In a multi tenant Kubeflow installation, the pods created by pipelines workflow and the pipelines frontend services run in an user profile namespace. The service account (`default-editor`) used for these pods needs permissions for the S3 bucket used by pipelines to read and write artifacts from S3. When using IRSA (IAM roles for service accounts) as your `PIPELINE_S3_CREDENTIAL_OPTION`, any additional profiles created as part of a multi-user deployment besides the preconfigured `kubeflow-user-example-com` will need to be configured with permissions to S3 bucket using IRSA.

The `default-editor` SA needs to be annotated with an IAM role with sufficient permissions to access your S3 Bucket to run your pipelines. In the below steps we will be configuring a profile an IAM role with restricted access to a specific S3 Bucket using the `AwsIamForServiceAccount` plugin for Profiles. To learn more about the `AwsIamForServiceAccount` plugin for Profiles read the [Profiles component guide]({{< ref "/docs/component-guides/profiles.md" >}}).

> Note: If you choose to run your pipeline with a service account other than the default which is `default-editor`, you must make sure to annotate that service account with an IAM role with sufficient S3 permissions.

## Create a Profile

After installing Kubeflow on AWS with one of the available [deployment options]({{< ref "/docs/deployment" >}}), you can configure Kubeflow Profiles with the following steps:

1. Define the following environment variables:
   
   The `S3_BUCKET` that is exported should be the same bucket that is used by Kubeflow Pipelines.
   ```bash
   # Your cluster name
   export CLUSTER_NAME=
   # Your cluster region
   export CLUSTER_REGION=
   # The S3 Bucket that is used by Kubeflow Pipelines
   export S3_BUCKET=
   # Your AWS Acconut ID
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
   # Name of the profile to create
   export PROFILE_NAMESPACE=
   ```
2. Retrieve OIDC Provider URL

   ```bash
   aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

   export OIDC_URL=$(aws eks describe-cluster --region $CLUSTER_REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)
   ```

3. Create an IAM trust policy to authorize federated requests from the OIDC provider.

   ```bash

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
           "${OIDC_URL}:sub": "system:serviceaccount:${PROFILE_NAMESPACE}:default-editor"
           }
       }
       }
   ]
   }
   EOF
   ```

4. [Create an IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html) with access to the S3 bucket where pipeline artifacts will be stored. The following policy grants full access to the S3 bucket, you can scope it down by giving read, write and GetBucketLocation permissions.
    ```bash
    cat <<EOF > s3_policy.json
    {
        "Version": "2012-10-17",
        "Statement": [
               {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::${S3_BUCKET}",
                "arn:aws:s3:::${S3_BUCKET}/*"
                  ]
               }
         ]
    }
    EOF
    ```
5. [Create an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html) for the Profile using the scoped policy from the previous step.

   ```bash
    aws iam create-role --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

    aws --region $CLUSTER_REGION iam put-role-policy --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --policy-name kf-$PROFILE_NAMESPACE-pipeline-s3 --policy-document file://s3_policy.json  
    ```

6. Create a user in your configured auth provider (e.g. Cognito or Dex).

   Export the user email as env variable, e.g. `user@example.com`

   ```bash
   export PROFILE_USER=""
   ```

7. Create a Profile using the `PROFILE_NAMESPACE`.

> Note: annotateOnly has been set to true. This means that the Profile Controller will not mutate your IAM Role and Policy.
   ```bash
   cat <<EOF > profile_iam.yaml
   apiVersion: kubeflow.org/v1
   kind: Profile
   metadata:
     name: ${PROFILE_NAMESPACE}
   spec:
     owner:
       kind: User
       name: ${PROFILE_USER}
     plugins:
     - kind: AwsIamForServiceAccount
       spec:
         awsIamRole: $(aws iam get-role --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --output text --query 'Role.Arn')
         annotateOnly: true
   EOF

   kubectl apply -f profile_iam.yaml
   ```