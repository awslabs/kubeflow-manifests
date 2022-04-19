+++
title = "AWS-Optimized Notebooks"
description = "Work in AWS-optimized Kubeflow Notebooks based on AWS Deep Learning Containers"
weight = 10
+++

Kubeflow on AWS includes AWS-optimized container images as default options for a Kubeflow Jupyter Notebook server. For more information on gettings started with Kubeflow Notebooks, see the [Quickstart Guide](https://www.kubeflow.org/docs/components/notebooks/quickstart-guide/).

## About Kubeflow Notebooks 

[Kubeflow Notebooks](https://www.kubeflow.org/docs/components/notebooks/) provide a way to run web-based development environments inside your Kubernetes cluster by running them inside Pods. Users can create Notebook containers directly in the cluster, rather than locally on their workstations. Access control is managed by Kubeflow’s RBAC, enabling easier notebook sharing across the organization.

For authentication, Kubeflow assigns the default-editor ServiceAccount to the Notebook Pods which is bound to the kubeflow-edit ClusterRole, which has namespace-scoped permissions to many Kubernetes resources. Because every Notebook Pod has the highly-privileged default-editor Kubernetes ServiceAccount bound to it, you can run kubectl inside it without providing additional authentication. Along the same lines you could use these notebooks to manage kubeflow pipeline runs and can also integrate with Tensorboard and the Visualization server. Also, you could use both EFS and FSx to replace the default persistentVolumes used as the workspace and/or data volume mounted onto the notebooks to enjoy sharing data and models across nodes as well as dynamic volume sizing. 

To facilitate the above features particularly access control and the possibility of sharing data admins can provide standard notebook images for their organization with required packages pre-installed. To help get you started, we have developed several such images on top of our AWS optimized Deep Learning Containers. These come packaged with the latest versions of AWS optimized frameworks such as Tensorflow and Pytorch and are available in both CPU and Cuda flavors. Moreover, they come with several useful AWS libraries such as boto3 and awscli, enabling you to directly access other AWS services such as S3 and IAM from the notebooks. 

## AWS-optimized container images

The following container images are available from the [Amazon Elastic Container Registry (Amazon ECR)](https://gallery.ecr.aws/c9e4w0g3/).

```
public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.0-gpu-py38-cu112
public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.0-cpu-py38
public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.9.0-gpu-py38-cu111
public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.9.0-cpu-py38
```

These images are based on [AWS Deep Learning Containers](https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/what-is-dlc.html). AWS Deep Learning Containers provide optimized environments with popular machine learning frameworks such as TensorFlow and PyTorch, and are available in the Amazon ECR. For more information on AWS Deep Learning Container options, see [Available Deep Learning Containers Images](https://github.com/aws/deep-learning-containers/blob/master/available_images.md).

Along with specific machine learning frameworks, these container images have additional pre-installed packages:
- `kfp`
- `kfserving` 
- `h5py`
- `pandas`
- `awscli`
- `boto3`

## AWS IAM for Kubeflow Profiles in Notebooks

Use AWS IAM to securely access AWS resources through Kubeflow Notebooks.

### Configuration

Prerequisites for setting up AWS IAM for Kubeflow Profiles can be found in the [Profiles](/docs/components/profiles/) component guide. The prerequisite steps will go through creating a profile that uses the AwsIamForServiceAccount plugin.
No additional configuration steps are required.

### Try it out

1. Create a notebook server through the central dashboard.
2. Select the profile name from the top left drop down menu for the profile you created.
3. Create a notebook from the sample (https://github.com/awslabs/kubeflow-manifests/blob/main/docs/component-guides/samples/notebooks/verify_profile_iam_notebook.ipynb).
4. Run the notebook, it should be able to list the S3 buckets present in your account.

