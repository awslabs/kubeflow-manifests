+++
title = "SageMaker Operators for Kubernetes (ACK)"
description = "Use SageMaker Operators for Kubernetes (ACK) with Kubeflow on AWS"
weight = 10
+++

[SageMaker Operators for Kubernetes (ACK)](https://github.com/aws-controllers-k8s/sagemaker-controller) make it easier for developers and data scientists using Kubernetes to train, tune, and deploy machine learning (ML) models using Amazon SageMaker. [ACK](https://aws-controllers-k8s.github.io/community/docs/community/overview/) lets you define and use AWS service resources directly from Kubernetes. With ACK, you can take advantage of AWS-managed services for your Kubernetes applications without needing to define resources outside of the cluster or run services that provide supporting capabilities like databases or message queues within the cluster.

## Tutorials

SageMaker Operators for Kubernetes (ACK) comes installed with all [deployment options]({{< ref "../deployment/_index.md" >}}) for Kubeflow on AWS.

For examples on using the SageMaker Operators for Kubernetes (ACK), see the following tutorials:
- [Machine Learning with the ACK SageMaker Controller](https://aws-controllers-k8s.github.io/community/docs/tutorials/sagemaker-example/#train-an-xgboost-model)

Use SageMaker Operators for Kubernetes (ACK) to manage your SageMaker resources from your Kubernetes cluster directly or from AWS-optimized [Kubeflow Notebooks]({{< ref "/docs/component-guides/notebooks.md" >}}) that are built on top of [AWS Deep Learning Containers](https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/what-is-dlc.html).

