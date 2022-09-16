+++
title = "Prerequisites"
description = "Set up your environment for deploying Kubeflow on AWS"
weight = 10
+++

## Create a Ubuntu environment

To get started with automated deployment, you must have a Ubuntu environment using one of the following methods:
- [Option 1: Amazon EC2]({{< ref "#amazon-ec2.md" >}})
- [Option 2: Docker]({{< ref "#docker.md" >}}) 
- [Option 3: AWS Cloud9]({{< ref "#aws-cloud9.md" >}})

### Option 1: Amazon EC2

Launch a Ubuntu-based Amazon EC2 instance. We recommend using a Ubuntu AWS Deep Learning AMI (DLAMI), such as the [AWS Deep Learning Base AMI (Ubuntu 18.04)](https://aws.amazon.com/releasenotes/aws-deep-learning-base-ami-ubuntu-18-04/) for your EC2 instance. To quickly get started with a DLAMI on Amazon EC2, see [Launch an AWS Deep Learning AMI](https://aws.amazon.com/getting-started/hands-on/get-started-dlami/). 

For more information about DLAMI options, see [Release Notes for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html). For information on instance type selection, see [Selecting the Instance Type for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/instance-select.html).

### Option 2: Docker

Create a Ubuntu environment using Docker. Pull the latest version of the Ubuntu image of your choice. For more information, see [Pull an image by digest (immutable identifier)](https://docs.docker.com/engine/reference/commandline/pull/#pull-an-image-by-digest-immutable-identifier) in the Docker documentation.
```sh
docker pull ubuntu:18.04
```

Connect to localhost from your container:
```sh
docker container run -it -p 127.0.0.1:8080:8080 ubuntu:18.04
```

Download the latest package information: 
```sh
apt update
```

 Install the necessary tools: 
```sh
apt install git curl unzip tar make sudo vim wget -y
```

### Option 3: AWS Cloud9

Launch a Ubuntu instance using Cloud9:
```sh
Launch Ubuntu 18.04 cloud9 instance 
```

## Clone the repository 

Clone the [`awslabs/kubeflow-manifests`](https://github.com/awslabs/kubeflow-manifests) and the [`kubeflow/manifests`](https://github.com/kubeflow/manifests) repositories and check out the release branches of your choosing.

Substitute the value for `KUBEFLOW_RELEASE_VERSION`(e.g. v1.6.0) and `AWS_RELEASE_VERSION`(e.g. v1.6.1-aws-b1.0.1) with the tag or branch you want to use below. Read more about [releases and versioning]({{< ref "/docs/about/releases.md" >}}) if you are unsure about what these values should be.
```bash
export KUBEFLOW_RELEASE_VERSION=v1.6.0
export AWS_RELEASE_VERSION=main
git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests
git checkout ${AWS_RELEASE_VERSION}
git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream
```

## Install the necessary tools 

Install the necessary tools with the following command: 
[TO DO: Where is this command located in the repo?]
```sh
make install-all-prerequisites
```

The command above installs the following tools: 
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
- [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
- [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
- [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://github.com/mikefarah/yq/#install))
- [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
- [kustomize version 3.2.0](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0) - A command line tool to customize Kubernetes objects through a kustomization file.
> Warning: Kubeflow is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order that resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know that this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.
- [python 3.8+](https://www.python.org/downloads/) - A programming language used for automated installation scripts.
- [pip](https://pip.pypa.io/en/stable/installation/) - A package installer for python.

## Create an EC2 Cluster
> Note : You do not need to create an EKS cluster if you are using Terraform

Use the following command to automatically provision an EKS cluster:
```sh
make
```

[What are the default settings/instance types, etc for this make command?]

> Note: Be sure to check [Amazon EKS and Kubeflow Compatibility]({{< ref "/docs/about/eks-compatibility.md" >}}) when creating your cluster with specific EKS versions.

If you do not want to use the default settings, you can create a customized EKS cluster with the following commands:

> Note: Various controllers use IAM roles for service accounts (IRSA). An [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) must exist for your cluster to use IRSA.

Change the values for the `CLUSTER_NAME` and `CLUSTER_REGION` environment variables: 
```bash
export CLUSTER_NAME=$CLUSTER_NAME
export CLUSTER_REGION=$CLUSTER_REGION
```

Run the following command to create an EKS cluster:
```bash
eksctl create cluster \
--name ${CLUSTER_NAME} \
--version 1.21 \
--region ${CLUSTER_REGION} \
--nodegroup-name linux-nodes \
--node-type m5.xlarge \
--nodes 5 \
--nodes-min 5 \
--nodes-max 10 \
--managed \
--with-oidc
```

If you are using an existing EKS cluster, create an [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) and associate it with for your EKS cluster with the following command:
```bash
eksctl utils associate-iam-oidc-provider --cluster ${CLUSTER_NAME} \
--region ${CLUSTER_REGION} --approve
```
More details about cluster creation via `eksctl` can be found in the [Creating and managing clusters](https://eksctl.io/usage/creating-and-managing-clusters/) guide.