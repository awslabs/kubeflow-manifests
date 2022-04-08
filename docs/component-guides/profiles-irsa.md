# IAM Role Service Accounts (IRSA) support for Kubeflow Profiles

# Background

In AWS, [IRSA](https://aws.amazon.com/blogs/opensource/introducing-fine-grained-iam-roles-service-accounts/) is a permissions management tool that allows applying AWS IAM permissions boundaries to Kubernetes service accounts (SA). This is useful, for example, to grant one SA permissions to upload test results to a certain bucket in S3 while granting another SA permissions to read from that bucket without modifying the contents. Because the IAM permissions apply to the SA, the permissions boundary is limited to the pod level rather than the nodegroup level. 

In Kubeflow, IRSA is used to provide an isolation boundary at the profile level, allowing admins to scope profiles to their necessary IAM permissions to meet their AWS usage requirements. This is done by making the profile SA an IRSA.

Below are the steps to configure IRSA to be used with Kubeflow Profiles.

# Configuration Steps

1. Export the following variables for convenience
    ```
    export CLUSTER_NAME=<your cluster name>
    export REGION=<your region>
    export AWS_ACCOUNT_ID=<your aws account id>
    export PROFILE_NAME=<the name of the profile to be created>
    ```

1. Create an IAM policy using [the following policy document](../../awsconfigs/infra_configs/iam_profile_controller_policy.json)
    ```
    aws iam create-policy \
    --region $REGION \
    --policy-name kf-profile-controller-policy \
    --policy-document file://awsconfigs/infra_configs/iam_profile_controller_policy.json
    ```

1. Create an IRSA for the profile controller using the policy
    ```
    eksctl create iamserviceaccount \
    --cluster=$CLUSTER_NAME \
    --name="profiles-controller-service-account" \
    --namespace=kubeflow \
    --attach-policy-arn="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/kf-profile-controller-policy" \
    --region=$REGION \
    --override-existing-serviceaccounts \
    --approve
    ```

1. Associate IAM OIDC with the cluster
    ```
    aws --region $REGION eks update-kubeconfig --name $CLUSTER_NAME

    eksctl utils associate-iam-oidc-provider --cluster $CLUSTER_NAME --region $REGION --approve
    ```

1. Create an IAM trust policy to authorize federated requests from the OIDC provider
    ```
    export OIDC_URL=$(aws eks describe-cluster --region $REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)

    cat <<EOF > trust.json
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Effect": "Allow",
        "Principal": {
            "Federated": "arn:aws:iam::${AWS_ACC_NUM}:oidc-provider/${OIDC_URL}"
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

1. Configure the profile user credentials via your auth provider
   - If using `Dex` add the following user to the base deployment config map:
     ```
       - email: $PROFILE_NAME@kubeflow.org
         hash: $2y$12$4K/VkmDd1q1Orb3xAt82zu8gk7Ad6ReFR4LCP9UeYE90NLiN9Df72 # 12341234
         username: $PROFILE_NAME
         userID: "15841185641789"
     ```
   - If using `AWS Cognito` see the following documentation to create a user pool and add users `https://docs.aws.amazon.com/cognito/latest/developerguide/getting-started-with-cognito-user-pools.html`

1. Create a profile using the `PROFILE_NAME` and `OIDC_ROLE_ARN`
    ```
    cat <<EOF > profile_iam.yaml
    apiVersion: kubeflow.org/v1
    kind: Profile
    metadata:
    name: $PROFILE_NAME
    spec:
    owner:
        kind: User
        name: $PROFILE_NAME@kubeflow.org
    plugins:
    - kind: AwsIamForServiceAccount
        spec:
        awsIamRole: $OIDC_ROLE_ARN
    EOF
    ```

1. Deploy kubeflow via the available [deployment options](../../docs/deployment) or re-deploy the `profiiles-controller` pod to apply the profile configurations.

# Verify Profiles IRSA in Notebooks
1. Create a notebook server through the central dashboard.
1. Create a notebook from [docs/component-guides/samples/profiles-irsa/verify_notebook.ipynb]()
1. Run the notebook, there should be no errors.





