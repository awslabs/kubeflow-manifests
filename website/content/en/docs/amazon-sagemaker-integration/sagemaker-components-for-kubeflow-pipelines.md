+++
title = "SageMaker Components for Kubeflow Pipelines"
description = "Use SageMaker Components for Kubeflow Pipelines with Kubeflow on AWS"
weight = 20
+++

The [SageMaker Components for Kubeflow Pipelines](https://docs.aws.amazon.com/sagemaker/latest/dg/kubernetes-sagemaker-components-for-kubeflow-pipelines.html) allow you to move your data processing and training jobs from the Kubernetes cluster to SageMaker’s machine learning-optimized managed service. 

These components integrate SageMaker with the portability and orchestration of Kubeflow Pipelines. Using the SageMaker components, each of the jobs in the pipeline workflow runs on SageMaker instead of the local Kubernetes cluster. The job parameters, status, logs, and outputs from SageMaker are still accessible from the Kubeflow Pipelines UI. The following SageMaker components have been created to integrate six key SageMaker features into your ML workflows. You can create a Kubeflow Pipeline built entirely using these components, or integrate individual components into your workflow as needed.

* [Training](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/train)
* [Hyperparameter Optimization](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/hyperparameter_tuning)
* [Processing](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/process)
* [Hosting Deploy](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/deploy)
* [Batch Transform component](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/batch_transform)
* [Ground Truth](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/ground_truth)
* [Workteam](https://github.com/kubeflow/pipelines/tree/master/components/aws/sagemaker/workteam)

To make it easier to try these componets out, the Kubeflow distribition for AWS includes pipeline tutorials for these SageMaker components. Examples have been included for the most common features that can be used to run production loads with just a few clicks. 

To try it out, deploy kubeflow on your cluster using the provided guides. Once installed, visit the Kubeflow Dashboard, `Pipelines` tab.