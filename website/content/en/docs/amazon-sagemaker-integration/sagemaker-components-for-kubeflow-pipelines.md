+++
title = "SageMaker Components for Kubeflow Pipelines"
description = "Use SageMaker Components for Kubeflow Pipelines with Kubeflow on AWS"
weight = 20
+++

The [SageMaker Components for Kubeflow Pipelines](https://docs.aws.amazon.com/sagemaker/latest/dg/kubernetes-sagemaker-components-for-kubeflow-pipelines.html) allow you to move your data processing and training jobs from the Kubernetes cluster to SageMaker’s machine learning-optimized managed service. 

These components integrate SageMaker with the portability and orchestration of Kubeflow Pipelines. Using the SageMaker components, each job in the pipeline workflow runs on SageMaker instead of the local Kubernetes cluster. The job parameters, status, logs, and outputs from SageMaker are accessible from the Kubeflow Pipelines UI. 

## Available components

You can create a Kubeflow Pipeline built entirely using SageMaker components, or integrate individual components into your workflow as needed. Available Amazon SageMaker components can be found in the [Kubeflow Pipelines GitHub repository](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker).

There are two versions of SageMaker components - boto3 based v1 components and SageMaker Operator for K8s (ACK) based v2 components. 

## Tutorial: SageMaker Training Pipeline for MNIST Classification with K-Means

Kubeflow on AWS includes pipeline tutorials for SageMaker components that can be used to run a machine learning workflow with just a few clicks. To try out the examples, deploy Kubeflow on AWS on your cluster and visit the Kubeflow Dashboard `Pipelines` tab. The sample currently included with Kubeflow is based off of the v2 Training Component.

In the following section we will walk through the steps to run the Sample SageMaker Training Pipeline. This sample runs a pipeline to train a classficiation model using Kmeans with MNIST dataset on SageMaker. This example was taken from an existing [SageMaker example](https://github.com/aws/amazon-sagemaker-examples/blob/8279abfcc78bad091608a4a7135e50a0bd0ec8bb/sagemaker-python-sdk/1P_kmeans_highlevel/kmeans_mnist.ipynb) and modified to work with the Amazon SageMaker Components for Kubeflow Pipelines. 

Note:  The pipeline runs are executed in user namespaces using the default-editor Kubernetes service account.

## Installing Kubeflow Pipelines
There are two ways to deploy Kubeflow Pipelines on AWS. If you are using the broader Kubeflow deployment, ACK and KFP come configured and ready to use with any of the Kubeflow on AWS deployment options. Read on to complete the pipeline execution. 

On the other hand, if you are using standalone KFP installation, please refer to our more detailed instructions over at the [AWS Docs for Kubeflow Pipeline Components](https://docs.aws.amazon.com/sagemaker/latest/dg/kubernetes-sagemaker-components-for-kubeflow-pipelines.html).

## S3 Bucket
To train a model with SageMaker, we need an S3 bucket to store the dataset and artifacts from the training process. Run the following commands to create an S3 bucket. Specify the value for `SAGEMAKER_REGION` as the region you want to create your SageMaker resources. For ease of use in the samples (using the default values of the pipeline), we suggest using `us-east-1` as the region.

```
# Choose any name for your S3 bucket
export SAGEMAKER_REGION=us-east-1
export S3_BUCKET_NAME=<bucket_name>

if [[ $SAGEMAKER_REGION == "us-east-1" ]]; then
    aws s3api create-bucket --bucket ${S3_BUCKET_NAME} --region ${SAGEMAKER_REGION}
else
    aws s3api create-bucket --bucket ${S3_BUCKET_NAME} --region ${SAGEMAKER_REGION} \
    --create-bucket-configuration LocationConstraint=${SAGEMAKER_REGION}
fi

echo ${S3_BUCKET_NAME}
```
Note down your S3 bucket name which will be used in the samples.

## SageMaker execution IAM role
The SageMaker training job needs an IAM role to access Amazon S3 and SageMaker. Run the following commands to create a SageMaker execution IAM role that is used by SageMaker to access AWS resources:

```
# Choose any name for your Sagemaker execution role
export SAGEMAKER_EXECUTION_ROLE_NAME=<sagemaker_role_name>

TRUST="{ \"Version\": \"2012-10-17\", \"Statement\": [ { \"Effect\": \"Allow\", \"Principal\": { \"Service\": \"sagemaker.amazonaws.com\" }, \"Action\": \"sts:AssumeRole\" } ] }"
aws iam create-role --role-name ${SAGEMAKER_EXECUTION_ROLE_NAME} --assume-role-policy-document "$TRUST"
aws iam attach-role-policy --role-name ${SAGEMAKER_EXECUTION_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess
aws iam attach-role-policy --role-name ${SAGEMAKER_EXECUTION_ROLE_NAME} --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

export SAGEMAKER_EXECUTION_ROLE_ARN=$(aws iam get-role --role-name ${SAGEMAKER_EXECUTION_ROLE_NAME} --output text --query 'Role.Arn')

echo $SAGEMAKER_EXECUTION_ROLE_ARN
```
Note down the execution role ARN to use in samples.



## Prepare the dataset

To train a model with SageMaker, we need an S3 bucket to store the dataset and artifacts from the training process. We will use the S3 bucket you created earlier and simply use the dataset at `s3://sagemaker-sample-files/datasets/image/MNIST/mnist.pkl.gz`.

1. Clone this repository to use the pipelines and sample scripts.
    ```
    git clone https://github.com/awslabs/kubeflow-manifests.git
    cd tests/e2e
    ```
1. Run the following commands to install the script dependencies and upload the processed dataset to your S3 bucket:
    ```
    pip install -r requirements.txt
    python3 utils/s3_for_training/sync.py ${S3_BUCKET_NAME} ${SAGEMAKER_REGION}
    ```

## Run the sample pipeline

1. To run the pipeline, open the Pipelines Tab on the Kubeflow dashboard. You should be able to see the pipeline sample called - "[Tutorial] SageMaker Training". Select to run. Make sure to either create a new experiment or use an existing one. 

2. In order to run the pipeline successfully you will have to provide the following two parameters value at a minimum based on the resources we created above. Feel free to tweak any other parameters as you see fit.  

```
s3_bucket_name: <S3_BUCKET_NAME>
sagemaker_role_arn: <SAGEMAKER_EXECUTION_ROLE_ARN>
region: us-east-1
```
> Note: The default value for the Training Image in the sample is for us-east-1. If you are not using `us-east-1` region you will have to find an training image URI according to the region. https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-algo-docker-registry-paths.html. For e.g.: for `us-west-2` the image URI is 174872318107.dkr.ecr.us-west-2.amazonaws.com/kmeans:1

3. Once the pipeline completes, you can see the outputs under 'Output parameters' in the Training component's Input/Output section.
