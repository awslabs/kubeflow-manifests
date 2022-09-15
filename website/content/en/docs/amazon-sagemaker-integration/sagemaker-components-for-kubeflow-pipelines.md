+++
title = "SageMaker Components for Kubeflow Pipelines"
description = "Use SageMaker Components for Kubeflow Pipelines with Kubeflow on AWS"
weight = 20
+++

The [SageMaker Components for Kubeflow Pipelines](https://docs.aws.amazon.com/sagemaker/latest/dg/kubernetes-sagemaker-components-for-kubeflow-pipelines.html) allow you to move your data processing and training jobs from the Kubernetes cluster to SageMaker’s machine learning-optimized managed service. 

These components integrate SageMaker with the portability and orchestration of Kubeflow Pipelines. Using the SageMaker components, each job in the pipeline workflow runs on SageMaker instead of the local Kubernetes cluster. The job parameters, status, logs, and outputs from SageMaker are accessible from the Kubeflow Pipelines UI. 

## Available components

You can create a Kubeflow Pipeline built entirely using SageMaker components, or integrate individual components into your workflow as needed. The following SageMaker components are available:

* [Training](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/train)
* [Hyperparameter Optimization](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/hyperparameter_tuning)
* [Processing](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/process)
* [Hosting Deploy](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/deploy)
* [Batch Transform component](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/batch_transform)
* [Ground Truth](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/ground_truth)
* [Workteam](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/workteam)

## Tutorials

Kubeflow on AWS includes pipeline tutorials for SageMaker components. Examples are included for the most common features that can be used to run production loads with just a few clicks. To try out the examples, deploy Kubeflow on AWS on your cluster and visit the Kubeflow Dashboard `Pipelines` tab.

To train a classficiation model using SageMaker Components for Kubeflow Pipelines, see the [MNIST classification with KMeans](https://github.com/kubeflow/pipelines/tree/master/samples/contrib/aws-samples/mnist-kmeans-sagemaker) sample. 