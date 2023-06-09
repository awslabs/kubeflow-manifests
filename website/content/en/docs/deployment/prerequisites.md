+++
title = "Prerequisites"
description = "Set up your environment for deploying Kubeflow on AWS"
weight = 10
+++

For all Kubeflow on AWS deployment options, you need to [create a Ubuntu environment]({{< ref "#create-ubuntu-environment" >}}), [clone the necessary repositories]({{< ref "#clone-repository" >}}), and [install the necessary tools]({{< ref "#install-necessary-tools" >}}). 

## Create Ubuntu environment

To get started with automated deployment, you must have a Ubuntu environment using one of the following methods:
- [Option 1: Amazon EC2]({{< ref "#amazon-ec2" >}})
- [Option 2: Docker]({{< ref "#docker" >}}) 
- [Option 3: AWS Cloud9]({{< ref "#aws-cloud9" >}})

### Option 1: Amazon EC2

Launch a Ubuntu-based Amazon EC2 instance. We recommend using a Ubuntu AWS Deep Learning AMI (DLAMI), such as the [AWS Deep Learning Base AMI (Ubuntu 18.04)](https://aws.amazon.com/releasenotes/aws-deep-learning-base-ami-ubuntu-18-04/) for your EC2 instance. To quickly get started with a DLAMI on Amazon EC2, see [Launch an AWS Deep Learning AMI](https://aws.amazon.com/getting-started/hands-on/get-started-dlami/). 

For more information about DLAMI options, see [Release Notes for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html). For information on instance type selection, see [Selecting the Instance Type for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/instance-select.html).

### Option 2: Docker

Create a Ubuntu environment using Docker. Pull the latest version of the Ubuntu image of your choice.
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

## Clone repository 

Clone the [`awslabs/kubeflow-manifests`](https://github.com/awslabs/kubeflow-manifests) and the [`kubeflow/manifests`](https://github.com/kubeflow/manifests) repositories and check out the release branches of your choosing.

Substitute the value for `KUBEFLOW_RELEASE_VERSION`(e.g. v1.7.0) and `AWS_RELEASE_VERSION`(e.g. v1.7.0-aws-b1.0.2) with the tag or branch you want to use below. Read more about [releases and versioning]({{< ref "/docs/about/releases.md" >}}) if you are unsure about what these values should be.
```bash
export KUBEFLOW_RELEASE_VERSION=v1.7.0
export AWS_RELEASE_VERSION=v1.7.0-aws-b1.0.2
git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests
git checkout ${AWS_RELEASE_VERSION}
git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream
```

## Install necessary tools 

Install the necessary tools with the following command: 
```sh
make install-tools
```
```sh
# NOTE: If you have other versions of python installed 
# then make sure the default is set to python3.8
alias python=python3.8
```

The `make` command above installs the following tools: 
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
- [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
- [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
- [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://github.com/mikefarah/yq/#install))
- [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
- [kustomize version 5.0.1](https://github.com/kubernetes-sigs/kustomize/releases/tag/kustomize%2Fv5.0.1) - A command line tool to customize Kubernetes objects through a kustomization file.
- [python 3.8+](https://www.python.org/downloads/) - A programming language used for automated installation scripts.
- [pip](https://pip.pypa.io/en/stable/installation/) - A package installer for python.
- [terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) - An infrastructure as code tool that lets you develop cloud and on-prem resources.
- [helm](https://helm.sh/docs/intro/install/) - A package manager for Kubernetes

## Configure AWS Credentials and Region for Deployment

To access AWS services, you need an AWS account and setup IAM credentials. Follow [AWS CLI Configure Quickstart documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html) to setup your IAM credentials.

Your IAM user/role needs the necessary privileges to create and manage your cluster and dependencies.
You might want to grant `Administrative Privileges` as it will require access to multiple services.

Run the following command to configure AWS CLI:

> Warning [Cloud9](https://docs.aws.amazon.com/cloud9/latest/user-guide/security-iam.html) users: When configuring your IAM credentials on Cloud9, we recommend using a [profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-profiles). Click `Cancel` when a pop up "Could not update credentials" opens, then choose `Permanently disable` for the "Unable to update credentials" pop up.
```bash
aws configure --profile=kubeflow
# AWS Access Key ID [None]: <enter access key id>
# AWS Secret Access Key [None]: <enter secret access key>
# Default region name [None]: <AWS region>
# Default output format [None]: json

# Set the AWS_PROFILE variable with the profile above
export AWS_PROFILE=kubeflow
```

Once your configuration is complete, run `aws sts get-caller-identity` to verify that AWS CLI has access to your IAM credentials.

## Installation options
Kubeflow on AWS can be installed completely using terraform or using manifests(kustomize, helm). If you are looking to install using terraform, navigate directly to one of the Terraform deployment guides. To deploy using manifests, proceed to [Create an EKS Cluster guide]({{< ref "/docs/deployment/create-eks-cluster.md" >}})
