+++
title = "Configure inferenceService to Access AWS Services from KServe"
description = "Configuration for accessing AWS services for inference services such as pulling images from private ECR and downloading models from S3 bucket."
weight = 10
+++

## Access AWS Service from Kserve with IAM Roles for ServiceAccount（IRSA）
1. Export env values:
    ```bash
    export CLUSTER_NAME="<>"
    export CLUSTER_REGION="<>"
    export PROFILE_NAMESPACE=kubeflow-user-profile
    export SERVICE_ACCOUNT_NAME=aws-sa
    export ECR_IMAGE_URL="<>"
    export S3_BUCKET_URL="<>"
    ```


1. Create Service Account with IAM Role using [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html). The following command attaches both `AmazonEC2ContainerRegistryReadOnly` and `AmazonS3ReadOnlyAccess` IAM policies:
    ```
    eksctl create iamserviceaccount --name ${SERVICE_ACCOUNT_NAME} --namespace ${PROFILE_NAMESPACE} --cluster ${CLUSTER_NAME} --region ${CLUSTER_REGION} --attach-policy-arn=arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly --attach-policy-arn=arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess  --override-existing-serviceaccounts --approve
    ```
     > NOTE: You can use ECR (`AmazonEC2ContainerRegistryReadOnly`) and S3 (`AmazonS3ReadOnlyAccess`) ReadOnly managed policies. We recommend creating fine grained policy for production usecase. 

### Deploy models from S3 Bucket 
1. Create Secret with empty AWS Credential:
    ```sh
    cat <<EOF > secret.yaml
    apiVersion: v1
        kind: Secret
        metadata:
          name: aws-secret
          namespace: ${PROFILE_NAMESPACE}
          annotations:
            serving.kserve.io/s3-endpoint: s3.amazonaws.com
            serving.kserve.io/s3-usehttps: "1"
            serving.kserve.io/s3-region: ${CLUSTER_REGION}
        type: Opaque
        data:
          AWS_ACCESS_KEY_ID: ""
          AWS_SECRET_ACCESS_KEY: ""
    EOF

    kubectl apply -f secret.yaml
    ```
    > NOTE: The **empty** keys for `AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY` force it to add the env vars to the init containers but don't override the actual credentials from the IAM role (which happens if you add dummy values). These **empty** keys are needed for IRSA to work in current version and will not be needed in future release.

1. Attach secret to IRSA in your profile namespace:
    ```
    kubectl patch serviceaccount ${SERVICE_ACCOUNT_NAME} -n ${PROFILE_NAMESPACE} -p '{"secrets": [{"name": "aws-secret"}]}'
    ```


### Create an InferenceService
1. Specify the service account in the model server spec :
    ```yaml
    apiVersion: serving.kserve.io/v1beta1
    kind: InferenceService
    metadata:
      name: "sklearn-iris"
      namespace: ${PROFILE_NAMESPACE}
    spec:
      predictor:
        serviceAccountName: ${SERVICE_ACCOUNT_NAME}
        model:
          modelFormat:
            name: sklearn
          image: ${ECR_IMAGE_URL}
          storageUri: ${S3_BUCKET_URL}
    ```
    > NOTE: make sure you have workable image in ${ECR_IMAGE_URL} and model in ${S3_BUCKET_URL} for the inferenceService to work. Versioning of model and image must be consistent: eg. you can not use a v1 model then a v2 image.
1. Check the InferenceService status:
```sh
kubectl get inferenceservices sklearn-iris -n ${PROFILE_NAMESPACE}
NAME           URL                                                        READY   PREV   LATEST   PREVROLLEDOUTREVISION   LATESTREADYREVISION                    AGE
sklearn-iris   http://sklearn-iris.kubeflow-user-example-com.example.com   True           100                              sklearn-iris-predictor-default-00001   105s
```
