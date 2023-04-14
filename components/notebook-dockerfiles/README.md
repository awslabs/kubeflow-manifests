# AWS Optimized Container Images for Kubeflow Notebooks

The AWS Distribution of Kubeflow comes with four ready-to-use container images prebuilt on top of the [AWS Optimized Deep-Learning Containers](https://aws.amazon.com/machine-learning/containers/) for Tensorflow and Pytorch. 

## The AWS Images
This directory contains the source code for these jupyter images which is based on the Kubeflow guidelines on building custom images [here](https://v1-4-branch.kubeflow.org/docs/components/notebooks/custom-notebook/) as well as the existing sample Dockerfiles [here](https://github.com/kubeflow/kubeflow/tree/v1.5.0/components/example-notebook-servers). 

The following AWS Optimized container images are available from the [Amazon Elastic Container Registry](https://gallery.ecr.aws/kubeflow-on-aws/) (Amazon ECR).
```
public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-tensorflow:2.12.0-gpu-py310-cu118-ubuntu20.04-ec2-v1.0
public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-tensorflow:2.12.0-cpu-py310-ubuntu20.04-ec2-v1.0
public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-pytorch:2.0.0-gpu-py310-cu118-ubuntu20.04-ec2-v1.0
public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-pytorch:2.0.0-cpu-py310-ubuntu20.04-ec2-v1.0
```
These images are based on AWS Deep Learning Containers which provide optimized environments with popular machine learning frameworks such as TensorFlow and PyTorch, and are available in the Amazon ECR. For more information on AWS Deep Learning Container options, see [Deep Learning Container Docs](https://docs.aws.amazon.com/deep-learning-containers/latest/devguide/what-is-dlc.html).

Along with specific machine learning frameworks, these container images have additional pre-installed packages:
```
kfp
kfserving
awscli
boto3
```

## How to Use
Once you have completed your Kubeflow deployment following the instructions in our various READMEs and have access to the Kubeflow UI, you can follow the steps on this [existing guide](https://v1-4-branch.kubeflow.org/docs/components/notebooks/setup/) to launch a new notebook server. You shuold be able to see a dropdown list of available AWS images while configuring this notebook server - choose Tensorflow or Pytorch, CPU or GPU as per your requirements and get started. 


