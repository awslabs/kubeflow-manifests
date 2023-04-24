+++
title = "Pipeline Profiles"
description = "Use AWS IAM roles for service accounts with Kubeflow Profiles"
weight = 70
+++

### Pipeline S3 Credential Option IRSA (IAM roles for service accounts)
When using IRSA (IAM roles for service accounts) as your pipeline S3 credential option any additional profiles created as part of a multi-user deployment besides the preconfigured `kubeflow-user-example-com` will need to be configured with IRSA to access S3. As part of multi-user-isolation, every Pipeline run in Kubeflow Pipelines is ran in an individuals profile user-namespace. A `default-editor` service account exists in every Profile's namespace that is used to run Pipelines as-well as connect to S3. This `default-editor` SA needs to be annotated with an IAM role with sufficient permissions to access your S3 Bucket to run your Pipelines. In the below steps we will be configuring an IAM role with restricted access to a specific S3 Bucket, we recommend following the principle of least privileges. 

>Note: If you choose to run your pipeline with a service account other than the default which is `default-editor`, you must make sure to annotate that service account with an IAM role with sufficient S3 permissions.

### Admin considerations

- Kubeflow admins will need to create an IAM role for each Profile with the desired scoped permissions.
- The Profile controller does not have the permissions specified in the Profile roles.
- The Profile controller has permissions to modify the Profile roles, which it will do to grant assume role permissions to the `default-editor` service account (SA) present in the Profile's namespace.
- A `default-editor` SA exists in every Profile's namespace and will be annotated with the role ARN created for the profile. Pods annotated with the SA name will be granted the Profile role permissions.
- The `default-editor` SA is used by various services in Kubeflow to launch resources in Profile namespaces. However, not all services do this by default.

## Configuration steps

After installing Kubeflow on AWS with one of the available [deployment options]({{< ref "/docs/deployment" >}}), you can configure Kubeflow Profiles with the following steps:

1. Define the following environment variables:

   ```bash
   export CLUSTER_NAME=<your cluster name>
   export CLUSTER_REGION=<your region>
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
   export PROFILE_NAME=<the name of the profile to be created>
   ```
3. Associate IAM OIDC with your cluster.

   ```bash
   aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

   eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --region $CLUSTER_REGION --approve

   export OIDC_URL=$(aws eks describe-cluster --region $CLUSTER_REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)
   ```

5. Create an IAM trust policy to authorize federated requests from the OIDC provider.

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
           "${OIDC_URL}:aud": "sts.amazonaws.com"
           }
       }
       }
   ]
   }
   EOF
   ```

6. [Create an IAM policy](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_create.html) with access to the S3 bucket where pipeline artifacts will be stored. The following policy grants full access to the S3 bucket, you can scope it down by giving read, write and GetBucketLocation permissions.
    ```bash
    printf '{
        "Version": "2012-10-17",
        "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::${S3_BUCKET}",
                "arn:aws:s3::::${S3_BUCKET}/*"
                  ]
               }
            ]
         }
          ' > ./s3_policy.json
    ```
7. [Create an IAM role](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create.html) for the Profile using the scoped policy from the previous step.

   ```bash
    aws iam create-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

    aws --region $CLUSTER_REGION iam put-role-policy --role-name $PROFILE_NAME-$CLUSTER_NAME-role --policy-name kf-pipeline-s3 --policy-document file://s3_policy.json  
    ```

8. Create a user in your configured auth provider (e.g. Cognito or Dex) or use an existing user.

   Export the user as an environment variable. For simplicity, we will use the `user@example.com` user that is created by default by most of our provided deployment options.

   ```bash
   export PROFILE_USER="user@example.com"
   ```

9. Create a Profile using the `PROFILE_NAME`.

>Note: annotateOnly has been set to true. This means that the Profile Controller will not mutate your IAM Role and Policy.
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
     plugins:
     - kind: AwsIamForServiceAccount
       spec:
         awsIamRole: $(aws iam get-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --output text --query 'Role.Arn')
         annotateOnly: true
   EOF

   kubectl apply -f profile_iam.yaml
   ```