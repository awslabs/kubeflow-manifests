+++
title = "Automated Deployment Guide"
description = "Deploy Kubeflow with RDS and S3 automatically"
weight = 10
+++

This guide describes how to deploy the vanilla distribution of Kubeflow on AWS using automated setup. This vanilla version has minimal changes to the upstream Kubeflow manifests.

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites/automated.md" >}}) before working through this guide.

## Deploy credentials

[TODO @akartsky ]

```sh
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export AWS_SESSION_TOKEN=
```

## Clone the repository

[TODO @akartsky]

## Run `make` commands

```sh
export CLUSTER_NAME=
export CLUSTER_REGION=
```

```sh
make install-all-prerequisites
make [TODO @akartsky]
```

## Connect to the Kubeflow UI

Connect to the Kubeflow UI. Follow the steps relevant to the type of [Ubuntu environment]({{< ref "../prerequisites/automated#create-a-ubuntu-environment.md" >}}) you are working in. 

### Amazon EC2 

Run the following command on your EC2 instance:
```sh
make port-forward
```

Then, run the following command on your local machine:
```sh
* ssh -i <path-to-your-key-pem> -L 8080:localhost:8080 -N ubuntu@ec2-<your-ec2-ipv4-address-separated-by-hyphens>.compute-1.amazonaws.com -o ExitOnForwardFailure=yes
```

Open the localhost browser: [http://localhost:8080/](http://localhost:8080/).

### Docker

Run the following command:
```sh
make port-forward IP_ADDRESS=0.0.0.0
```

Open the localhost browser: [http://localhost:8080/](http://localhost:8080/).

### AWS Cloud9

```sh
make port-forward
```

Open the Cloud9 browser and go to: [http://localhost:8080/](http://localhost:8080/).

## Log in with Dex

Enter your Username and Password to start working in the Kubeflow UI.