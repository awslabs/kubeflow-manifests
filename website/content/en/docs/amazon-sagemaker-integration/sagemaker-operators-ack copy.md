+++
title = "SageMaker Operators for Kubernetes (ACK)"
description = "Use SageMaker Operators for Kubernetes (ACK) with Kubeflow on AWS"
weight = 10
+++

The [ACK Operators for SageMaker](https://aws-controllers-k8s.github.io/community/docs/tutorials/sagemaker-example/) make it easier for developers and data scientists using Kubernetes to train, tune, and deploy machine learning (ML) models in SageMaker. [ACK](https://aws-controllers-k8s.github.io/community/docs/community/overview/) lets you define and use AWS service resources directly from Kubernetes. With ACK, you can take advantage of AWS-managed services for your Kubernetes applications without needing to define resources outside of the cluster or run services that provide supporting capabilities like databases or message queues within the cluster.

The Kubeflow Distribution for AWS bundles with it kustomize and helm templates which make it easy to deploy the ACK operators for SageMaker. Once installed, you can use ACK to manage your SageMaker resources not only from your kubernetes cluster directly but also from the Kubeflow notebooks by spawning one of our AWS optimized DLC based images. 