+++
title = "Access AWS-Service from KServe using IRSA"
description = "Configuration for accessing AWS services for inference services such as pulling images for private ECR and downloading models from S3 bucket."
weight = 10
+++

## Access AWS Service from Kserve with IAM Roles for ServiceAccount（IRSA）
1. Create a policy with following AWS [ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/ECR_on_EKS.html) or [S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-policy-language-overview.html) permissions :
    Select the package manager of your choice.
    {{< tabpane persistLang=false >}}
    {{< tab header="ECR" lang="toml" >}}
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:GetAuthorizationToken"
                ],
                "Resource": "*"
            }
        ]
    }
    {{< /tab >}}
    {{< tab header="S3" lang="yaml" >}}
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "Example permissions",
                "Effect": "Allow",
                "Principal": {
                "AWS": "arn:aws:iam::123456789012:user/Dave"
                },
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                    "s3:GetObject"
                ],
                "Resource": [
                    "arn:aws:s3:::awsexamplebucket1"
                ]
            }
        ]
    }
    {{< /tab >}}
    {{< /tabpane >}}


1. Create Service Account with IAM Role using [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html):
    ```
    eksctl create iamserviceaccount --name access-aws-service-sa --namespace ${YOUR_PROFILE_NAMESPACE} --cluster ${CLUSTER_NAME} --region ${CLUSTER_REGION} --attach-policy-arn ${IAM_POLICY_ARN} --override-existing-serviceaccounts --approve
    ```

1. Specify this service account in the model server spec:
    ```yaml
    apiVersion: serving.kserve.io/v1beta1
    kind: InferenceService
    metadata:
    name: "mnist-s3"
    spec:
    transformer:
        serviceAccountName: access-aws-service-sa
        containers:
        - image: 80*********03.dkr.ecr.us-east-1.amazonaws.com/cnndha:image-transformer-v2
        name: kfserving-container
        env:
            - name: STORAGE_URI
            value: s3://kserve-examples/mnist
    predictor:
        tensorflow:
            storageUri: s3://kserve-examples/mnist
    ```

## Deploy models from S3 Bucket
1. Create Secret with empty AWS Credential:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
    name: aws-secret
    annotations:
        serving.kserve.io/s3-endpoint: s3.amazonaws.com
        serving.kserve.io/s3-usehttps: "1"
        serving.kserve.io/s3-region: us-east-1
    type: Opaque
    data:
    AWS_ACCESS_KEY_ID:
    AWS_SECRET_ACCESS_KEY:
    ```
    > NOTE: The empty keys for `AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY` force it to add the env vars to the init containers but don't override the actual credentials from the IAM role (which happens if you add dummy values)

1. Attach secret to IRSA:
    ```yaml
    apiVersion: v1
    kind: ServiceAccount
    metadata:
    name: access-aws-service-sa
    annotations:
        eks.amazonaws.com/role-arn: arn:aws:iam::etc
    secrets:
    - name: aws-secret
    ```

1. Deploy the model on S3:
    ```yaml
    apiVersion: "serving.kserve.io/v1beta1"
    kind: "InferenceService"
    metadata:
    name: "mnist-s3"
    spec:
        predictor:
            serviceAccountName: access-aws-service-sa
            tensorflow:
                storageUri: "s3://kserve-examples/mnist"
    ```