+++
title = "Terraform Deployment Guide"
description = "Deploy Kubeflow with Cognito, RDS, and S3 using Terraform"
weight = 30
+++

## Prerequisites

Be sure that you have satisfied the [installation prerequisites]({{< ref "../prerequisites.md" >}}) before working through this guide.

Specifially, you must:
- [Create a Ubuntu environment]({{< ref "../prerequisites/#create-a-ubuntu-environment.md" >}})
- [Clone the repository]({{< ref "../prerequisites/#clone-the-repository.md" >}})
- [Install the necessary tools]({{< ref "../prerequisites/#create-a-ubuntu-environment.md" >}})

## Deployment Steps

Export the following variables as inputs for the cluster to be created

```sh
export TF_VAR_cluster_name=<desired_cluster_name>
export TF_VAR_cluster_region=<desired_cluster_region>
```

Run the below command to deploy
```sh
make deploy
```

## Verification

The following steps will allow you to access the Kubeflow central dashboard from your browser.

#### Step 0: Update the kubeconfig
```sh
$(terraform output -raw configure_kubectl)
```

#### Step 1: Enable portforwarding for the central dashboard
```sh
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

#### [Optional] Step 2: Enable portfowarding from your EC2 instance

If you are running kubectl on an ec2 instance you will need to run the below command on your local machine to access the dashboard.
```sh
ssh -i your-ssh-key.pem -N -L 8080:localhost:8080 your-ec2-instance-username@your-ec2-instance-dns.us-west-2.compute.amazonaws.com
```

This is an extension of the ssh command used to ssh to the instance, so if your ssh command was:
```sh
ssh -i "key.pem" ubuntu@ec2-xx-xx-xxx-xx.us-west-2.compute.amazonaws.com
```

then you would run:
```sh
ssh -i "key.pem" -N -L 8080:localhost:8080 ubuntu@ec2-xx-xx-xxx-xx.us-west-2.compute.amazonaws.com
```

#### Step 3: Login to the central dashboard.

Open `http://localhost:8080` in a browser of your choosing.

Provide the following username and password at the login screen:
- Username: `user@example.com`
- Password: `12341234`

## Cleanup

```sh
make delete
```
