# IAM Role Service Accounts (IRSA) support for Kubeflow Profiles

# Background

In AWS, [IRSA](https://aws.amazon.com/blogs/opensource/introducing-fine-grained-iam-roles-service-accounts/) is a permissions management tool that allows applying AWS IAM permissions boundaries to Kubernetes service accounts (SA). This is useful, for example, to grant one SA permissions to upload test results to a certain bucket in S3 while granting another SA permissions to read from that bucket without modifying the contents. Because the IAM permissions apply to the SA, the permissions boundary is limited to the pod level rather than the nodegroup level. 

In Kubeflow, IRSA is used to provide an isolation boundary at the profile level, allowing admins to scope profiles to their necessary IAM permissions to meet their AWS usage requirements. This is done by making the profile SA an IRSA and by creating profiles with the `AwsIamForServiceAccount` plugin.

Below are the steps to configure IRSA to be used with Kubeflow Profiles.

# Configuration Steps

The following steps should be run after deploying Kubeflow via the [provided deployment options](../../docs/deployment)

1. Export the following variables for convenience
    ```
    export CLUSTER_NAME=<your cluster name>
    export CLUSTER_REGION=<your region>
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
    export PROFILE_NAME=<the name of the profile to be created>
    ```

1. Create an IAM policy using [the following policy document](../../awsconfigs/infra_configs/iam_profile_controller_policy.json)
    ```
    aws iam create-policy \
    --region $CLUSTER_REGION \
    --policy-name kf-profile-controller-policy \
    --policy-document file://awsconfigs/infra_configs/iam_profile_controller_policy.json
    ```

1. Associate IAM OIDC with the cluster
    ```
    aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

    eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --region $CLUSTER_REGION --approve
    ```

1. Create an IRSA for the profile controller using the policy.
    ```
    eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --name="profiles-controller-service-account" \
    --namespace=kubeflow \
    --attach-policy-arn="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/kf-profile-controller-policy" \
    --region=$CLUSTER_REGION \
    --override-existing-serviceaccounts \
    --approve
    ```

1. Create an IAM trust policy to authorize federated requests from the OIDC provider
    ```
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

1. Create an IAM policy to scope the permissions for the profile. For simplicity, we will use the `arn:aws:iam::aws:policy/AmazonS3FullAccess` policy as an example.

1. Create the IAM role to be used for the profile IRSA
    ```
    aws iam create-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

    aws iam attach-role-policy --role-name $PROFILE_NAME-$CLUSTER_NAME-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
    ```

1. Get the OIDC role arn for the created profile
    ```
    export OIDC_ROLE_ARN=$(aws iam get-role --role-name $PROFILE_NAME-$CLUSTER_NAME-role --output text --query 'Role.Arn')
    ```

1. Create a profile using the `PROFILE_NAME` and `OIDC_ROLE_ARN`
    ```
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
          awsIamRole: ${OIDC_ROLE_ARN}
    EOF

    kubectl apply -f profile_iam.yaml
    ```

# Verify Profiles IRSA in Notebooks
1. Create a notebook server through the central dashboard.
1. Select the profile owner from the top left drop down menu for the profile you created.
1. Create a notebook from [docs/component-guides/samples/profiles-irsa/verify_notebook.ipynb]()
1. Run the notebook, there should be no errors.





