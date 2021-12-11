# Deploying Kubeflow with AWS EFS as Persistent Storage

This guide describes how to use Amazon EFS as Persistent storage with Kubeflow.  

## 1.0 Prerequisites
1. For this README, we will assume that you already have an EKS Cluster with Kubeflow installed since the EFS CSI Driver can be installed and configured as a separate resource on top of an existing Kubeflow deployment. You can follow any of the other guides to complete these steps - choose one of the AWS managed service integrated offering<link> or generic distribution<link>.

2. At this point, you have likely cloned this repo and checked out the right branch. Navigate over this this directory. 

3. Make sure the following environment variables are set. 
```
export CLUSTER_NAME=<clustername>
export CLUSTER_REGION=<clusterregion>
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
```

## 2.0 Install the EFS CSI Driver
We recommend installing the EFS CSI Driver v1.3.4 directly from the [the aws-efs-csi-driver github repo](https://github.com/kubernetes-sigs/aws-efs-csi-driver) as follows - 

```
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=tags/v1.3.4"
```

You can confirm that EFS CSI Driver was installed into the default kube-system namespace for you. You can check using the following command - 
```
kubectl get csidriver

NAME              ATTACHREQUIRED   PODINFOONMOUNT   MODES        AGE
efs.csi.aws.com   false            false            Persistent   5d17h
```

## 3.0 Create the IAM Policy for the CSI Driver
The CSI driver's service account (created during installation) requires IAM permission to make calls to AWS APIs on your behalf. Here, we will be annotating the Service Account `efs-csi-controller-sa` with an IAM Role which has the required permissions.

1. Download the IAM policy document from GitHub as follows - 

```
curl -o iam-policy-example.json https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/v1.3.4/docs/iam-policy-example.json
```

2. Create the policy - 
```
aws iam create-policy \
    --policy-name AmazonEKS_EFS_CSI_Driver_Policy \
    --policy-document file://iam-policy-example.json
```

3. Create an IAM role and attach the IAM policy to it. Annotate the Kubernetes service account with the IAM role ARN and the IAM role with the Kubernetes service account name. You can create the role using eksctl as follows - 

```
eksctl create iamserviceaccount \
    --name efs-csi-controller-sa \
    --namespace kube-system \
    --cluster $CLUSTER_NAME \
    --attach-policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/AmazonEKS_EFS_CSI_Driver_Policy \
    --approve \
    --override-existing-serviceaccounts \
    --region $CLUSTER_REGION
```

4. You can verify by describing the specified service account to check if it has been correctly annotated - 
```
kubectl describe -n kube-system serviceaccount efs-csi-controller-sa
```

## 4.0 Create an Instance of the EFS Filesystem
Please refer to the official [AWS EFS CSI Document](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html#efs-create-filesystem) for detailed instructions on creating an EFS filesystem. 


## 5.0 Using EFS Storage in Kubeflow

## 5.1 Provisioning Options
### Option 1 - Static Provisioning
[Using this sample from official AWS Docs](https://github.com/kubernetes-sigs/aws-efs-csi-driver/tree/master/examples/kubernetes/multiple_pods) we have provided the required spec files in the sample subdirectory but you can create the PVC another way. 

1. Use the `$file_system_id` you recorded before or use the following command to get the efs filesystem id - 
```
aws efs describe-file-systems --query "FileSystems[*].FileSystemId" --output text
```

2. Now edit the last line of the sample/pv.yaml file to specify the `volumeHandle` field to point to your EFS filesystem.
```
yq e '.spec.csi.volumeHandle = env(file_system_id)' -i sample/pv.yaml
```

3. The `PersistentVolume` and `StorageClass` are cluster scoped resources but the `PersistentVolumeClaim` needs to be in the namespace you will be accessing it from. Be sure to replace the `kubeflow-user-example-com` namespace specified in the `sample/pvc.yaml` file with the namespace for the kubeflow user. 

4. Now create the required persistentvolume, persistentvolumeclaim and storageclass resources as -
```
kubectl apply -f examples/aws/storage-efs/sample/pv.yaml
kubectl apply -f examples/aws/storage-efs/sample/pvc.yaml
kubectl apply -f examples/aws/storage-efs/sample/sc.yaml
```

## 5.2 Check your Setup
Port Forward as needed and Login to the Kubeflow dashboard.
Now, Check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow. In the following two sections we will be using this PVC to create a notebook server with Amazon EFS mounted as the workspace volume, download training data into this filesystem and then deploy a TFJob to train a model using this data. 

## 5.3 Using EFS volume as workspace or data volume for a notebook server 

Spin up a new Kubeflow notebook server and specify the name of the PVC to be used as the workspace volume or the data volume and specify your desired mount point. For our example here, we are using the `AWS Optimized Tensorflow 2.6 CPU image` provided in the notebook configuration options. Additionally, use the existing `efs-claim` volume as the workspace volume at the default mount point `/home/jovyan`. The server might take a few minutes to come up. 

In case the server does not start up in the expected time, do make sure to check - 
1. The Notebook Controller Logs
2. The specific notebook server instance pod's logs

### Note about Permissions
You might need to specify some additional directory permissions on your worker node before you can use these as mount points. By default, new Amazon EFS file systems are owned by root:root, and only the root user (UID 0) has read-write-execute permissions. If your containers are not running as root, you must change the Amazon EFS file system permissions to allow other users to modify the file system. The set-permission-job.yaml is an example of how you could set these permissions to be able to use the efs as your workspace in your kubeflow notebook. 
```
kubectl apply -f examples/aws/storage-efs/sample/set-permission-job.yaml
```
If you use EFS for other purposes (e.g. sharing data across pipelines), you don’t need this step.

## 5.4 Using EFS volume for a TrainingJob using TFJob Operator
The following section re-uses the PVC and the Tensorflow Kubeflow Notebook created in the previous steps to download a dataset to the EFS Volume. Then we spin up a TFjob which runs a image classification job using the data from the shared volume. 
Source: https://www.tensorflow.org/tutorials/load_data/images

### 1. Download the dataset to the EFS Volume 
In the Kubeflow Notebook created above, use the following snippet to download the data into the `/home/jovyan/.keras` directory (which is mounted onto the EFS Volume). 
```
import pathlib
import tensorflow as tf
dataset_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
data_dir = tf.keras.utils.get_file(origin=dataset_url,
                                   fname='flower_photos',
                                   untar=True)
data_dir = pathlib.Path(data_dir)
```

### 2. Build and Push the Docker image
In the `training-sample` directory, we have provided a sample training script and Dockerfile which you can use as follows to build a docker image- 
```
export dockerImage=image-classification:no-data
cd examples/aws/storage-efs/training-sample
docker build -t $dockerImage .
docker push $dockerImage
```
Once the docker image is built, be sure to replace the `<dockerimage:tag>` in the `tfjob.yaml` file, line #17. 
```
yq e '.spec.tfReplicaSpecs.Worker.template.spec.containers[0].image = env(dockerImage)' -i training-sample/tfjob.yaml
```

### 3. Create the TFjob and use the provided commands to check the training logs 
At this point, we are ready to train the model using the `training.py` script and the data available on the shared volume with the Kubeflow TFJob operator as -
```
kubectl apply -f tfjob.yaml
```

In order to check that the training job is running as expected, you can check the events in the TFJob describe response as well as the job logs as - 
```
kubectl describe tfjob image-classification-pvc -n kubeflow-user-example-com
kubectl logs -n kubeflow-user-example-com image-classification-pvc-worker-0 -f
```
