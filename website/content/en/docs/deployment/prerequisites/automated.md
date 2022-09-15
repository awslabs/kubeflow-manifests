+++
title = "Prerequisites for Automated Deployment"
description = "Everything you need to get started with Kubeflow on AWS"
weight = 20
+++

Starting with v1.6, Kubeflow on AWS provides automated deployment for all of the integrated deployment options. 

## Create a Ubuntu environment

To get started with automated deployment, you must have a Ubuntu environment using one of the following methods:
- [Amazon EC2]({{< ref "#amazon-ec2.md" >}})
- [Docker]({{< ref "#docker.md" >}}) 
- [AWS Cloud9]({{< ref "#aws-cloud9.md" >}})

### Amazon EC2

Launch a Ubuntu-based Amazon EC2 instance. We recommend using a Ubuntu AWS Deep Learning AMI (DLAMI), such as the [AWS Deep Learning Base AMI (Ubuntu 18.04)](https://aws.amazon.com/releasenotes/aws-deep-learning-base-ami-ubuntu-18-04/) for your EC2 instance. To quickly get started with a DLAMI on Amazon EC2, see [Launch an AWS Deep Learning AMI](https://aws.amazon.com/getting-started/hands-on/get-started-dlami/). 

For more information about DLAMI options, see [Release Notes for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/appendix-ami-release-notes.html). For information on instance type selection, see [Selecting the Instance Type for DLAMI](https://docs.aws.amazon.com/dlami/latest/devguide/instance-select.html).

### Docker

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

### AWS Cloud9

Launch a Ubuntu instance using Cloud9:
```sh
Launch Ubuntu 18.04 cloud9 instance 
```

After you set up your Ubuntu environment, go through the Automated Deployment Guide for the [deployment option]({{< ref "/deployment.md" >}}) of your choice. 