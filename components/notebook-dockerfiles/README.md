# AWS Optimized Container Images for Kubeflow Notebooks

The AWS Distribution of Kubeflow comes with four ready-to-use container images prebuilt on top of the [AWS Optimized Deep-Learning Containers](https://aws.amazon.com/machine-learning/containers/) for Tensorflow and Pytorch. 

## Source
This directory contains the source code for these jupyter images which is based on the Kubeflow guidelines on building custom images [here](https://v1-4-branch.kubeflow.org/docs/components/notebooks/custom-notebook/) as well as the existing sample Dockerfiles [here](https://github.com/kubeflow/kubeflow/tree/v1.4-rc.1/components/example-notebook-servers). 

## How to Use
Once you have completed your Kubeflow deployment following the instructions in our various READMEs and have access to the Kubeflow UI, you can follow the steps on this [existing guide](https://v1-4-branch.kubeflow.org/docs/components/notebooks/setup/) to launch a new notebook server. You shuold be able to see a dropdown list of available AWS images while configuring this notebook server - choose Tensorflow or Pytorch, CPU or GPU as per your requirements and get started. 


