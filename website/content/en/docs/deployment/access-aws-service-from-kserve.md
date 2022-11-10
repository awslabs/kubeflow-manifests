+++
title = "Access AWS-Service from KServe"
description = "Configuration for accessing AWS services for inference services such as pulling images for private ECR and downloading models from S3 bucket."
weight = 10
+++

## Access AWS Service from Kserve with IAM Roles for ServiceAccount（IRSA）
1. Create a policy with following [permissions](https://docs.aws.amazon.com/AmazonECR/latest/userguide/ECR_on_EKS.html):
    ```
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
    ```

1. Create a IAM role and attach it to a service account using [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html):
    ```
    eksctl create iamserviceaccount --name image-pull-sa --namespace ${YOUR_PROFILE_NAMESPACE} --cluster ${CLUSTER_NAME} --region ${CLUSTER_REGION} --attach-policy-arn ${IAM_POLICY_ARN} --override-existing-serviceaccounts --approve
    ```

1. Specify this service account in the model server spec:
    ```
    apiVersion: serving.kserve.io/v1beta1
    kind: InferenceService
    metadata:
    name: torchserve-transformer
    spec:
    transformer:
        serviceAccountName: image-pull-sa
        containers:
        - image: 80*********03.dkr.ecr.us-east-1.amazonaws.com/cnndha:image-transformer-v2
        name: kfserving-container
        env:
            - name: STORAGE_URI
            value: gs://kfserving-examples/models/torchserve/image_classifier
    predictor:
        pytorch:
        storageUri: gs://kfserving-examples/models/torchserve/image_classifier
    ```

## Download models from S3 Bucket
1. Create Secret with empty AWS Credential:
    ```
    apiVersion: v1
    kind: Secret
    metadata:
    name: aws-secret
    annotations:
        serving.kserve.io/s3-endpoint: s3.amazonaws.com
        serving.kserve.io/s3-usehttps: "1"
        serving.kserve.io/s3-region: ap-southeast-2
    type: Opaque
    data:
    AWS_ACCESS_KEY_ID:
    AWS_SECRET_ACCESS_KEY:
    ```
    > NOTE: The empty keys for `AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY` force it to add the env vars to the init containers but don't override the actual credentials from the IAM role (which happens if you add dummy values)

1. Configure model-serving Service account with IRSA:
    ```
    apiVersion: v1
    kind: ServiceAccount
    metadata:
    name: model-serving
    annotations:
        eks.amazonaws.com/role-arn: arn:aws:iam::etc
    secrets:
    - name: aws-secret
    ```