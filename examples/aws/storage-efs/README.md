# Deploying Kubeflow with AWS EFS as Persistent Storage

This guide describes how to deploy Kubeflow on AWS EKS using EFS as the Persistent Storage. <complete intro>

## 1.0 Prerequisites

1. Install the CLI tools
2. Clone this repo and checkout the right branch
3. Create an EKS cluster and
4. Make sure the following environment variables are set - 
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

You should see the following resources get created - 
```
serviceaccount/efs-csi-controller-sa created
serviceaccount/efs-csi-node-sa created
clusterrole.rbac.authorization.k8s.io/efs-csi-external-provisioner-role created
clusterrolebinding.rbac.authorization.k8s.io/efs-csi-provisioner-binding created
deployment.apps/efs-csi-controller created
daemonset.apps/efs-csi-node created
csidriver.storage.k8s.io/efs.csi.aws.com configured
```

Additionally, you can confirm that EFS CSI Driver was installed into the default kube-system namespace for you. You can check using the following command - 
```
kubectl get csidriver

NAME              ATTACHREQUIRED   PODINFOONMOUNT   MODES        AGE
efs.csi.aws.com   false            false            Persistent   5d17h
```

## 3.0 Create the IAM Policy for the CSI Driver
The driver requires IAM permission to talk to Amazon EFS to manage the volume on user's behalf. Here, we will be creating/annotating the Service Account `efs-csi-controller-sa` with an IAM Role which has the required permissions.

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
kubectl describe -n kube-system serviceaccount efs-csi-controller-sa -n kube-system
```

## 4.0 Create an Instance of the EFS Filesystem
This section creates a new EFS volume using for your cluster. Please refer to the official [AWS Documents](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html) for more details. 

1. Retrieve the VPC ID that your cluster is in and store it in a variable for use in a later step.
```
vpc_id=$(aws eks describe-cluster \
    --name $CLUSTER_NAME\
    --query "cluster.resourcesVpcConfig.vpcId" \
    --output text)
```

2. Retrieve the CIDR range for your cluster's VPC and store it in a variable for use in a later step.
```
cidr_range=$(aws ec2 describe-vpcs \
    --vpc-ids $vpc_id \
    --query "Vpcs[].CidrBlock" \
    --output text)
```

3. Create a security group with an inbound rule that allows inbound NFS traffic for your Amazon EFS mount points.

    a. Create a security group. 
    ```
    security_group_id=$(aws ec2 create-security-group \
        --group-name MyEfsSecurityGroup \
        --description "My EFS security group" \
        --vpc-id $vpc_id \
        --output text)
    ```

    b. Create an inbound rule that allows inbound NFS traffic from the CIDR for your cluster's VPC.
    ```
    aws ec2 authorize-security-group-ingress \
        --group-id $security_group_id \
        --protocol tcp \
        --port 2049 \
        --cidr $cidr_range
    ```

4. Create an Amazon EFS file system for your Amazon EKS cluster.
```
file_system_id=$(aws efs create-file-system \
    --region $CLUSTER_REGION \
    --performance-mode generalPurpose \
    --query 'FileSystemId' \
    --output text)
```

## 5.0 Create Mount Targets for your cluster
1. [Optional] If you are re-using an existing EFS Volume, you will first have to delete any old mount targets. You can use the following commands for this - 
```
aws efs describe-mount-targets --file-system-id $file_system_id
aws efs delete-mount-target --mount-target-id <each-id>
```

2. Determine the IDs of the subnets in your VPC and which Availability Zone the subnet is in.
```
aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$vpc_id" \
    --query 'Subnets[*].{SubnetId: SubnetId,AvailabilityZone: AvailabilityZone,CidrBlock: CidrBlock}' \
    --output table
```

4. Add mount targets for the subnets that your nodes are in. If are more than 1 nodes in the cluster, you'd run the command once for a subnet in each AZ that you had a node in, replacing subnet-EXAMPLEe2ba886490 with the appropriate subnet ID from the previous command
```
aws efs create-mount-target \
    --file-system-id $file_system_id \
    --security-groups $security_group_id \
    --subnet-id <subnet-EXAMPLEe2ba886490>
```


## 6.0 Using EFS Storage in Kubeflow

## 6.1 Provisioning Options
### Option 1 - Static Provisioning
[Using this sample from official AWS Docs](https://github.com/kubernetes-sigs/aws-efs-csi-driver/tree/master/examples/kubernetes/multiple_pods) we have provided the required spec files in the sample subdirectory but you can create the PVC another way. 

1. Use the `$file_system_id` you recorded before or use the following command to get the efs filesystem id - 
```
aws efs describe-file-systems --query "FileSystems[*].FileSystemId" --output text
```

2. Now edit the sample/pv.yaml and edit the `volumeHandle` to point to your EFS filesystem

3. The `PersistentVolume` and `StorageClass` are cluster scoped resources but the `PersistentVolumeClaim` needs to be in the namespace you will be accessing it from. Be sure to replace the `kubeflow-user-example-com` namespace specified in the `sample/pvc.yaml` file if you are using a different one. 

4. Now create the required persistentvolume, persistentvolumeclaim and storageclass resources as -
```
kubectl apply -f examples/aws/storage-efs/sample/pv.yaml
kubectl apply -f examples/aws/storage-efs/sample/pvc.yaml
kubectl apply -f examples/aws/storage-efs/sample/sc.yaml
```

## 6.2 Check your Setup
Port Forward as needed and Login to the Kubeflow dashboard.
Now, Check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow. In the following two sections we will be using this PVC to create a notebook server with Amazon EFS mounted as the workspace volume, download training data into this filesystem and then deploy a TFJob to train a model using this data. 

## 6.3 Using EFS volume as workspace or data volume for a notebook server 

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

## 6.4 Using EFS volume for a TrainingJob using TFJob Operator
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
cd examples/aws/storage-efs/training-sample
docker build -t <dockerimage:tag>
docker push <dockerimage:tag>
```
Once the docker image is built, be sure to replace the `<dockerimage:tag>` in the `tfjob.yaml` file, line #17. 

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
