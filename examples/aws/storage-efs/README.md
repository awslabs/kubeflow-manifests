# Deploying Kubeflow with AWS EFS as Persistent Storage

This guide describes how to deploy Kubeflow on AWS EKS using EFS as the Persistent Storage. <complete intro>

## Prerequisites

This guide assumes that you have:

1. Installed the following tools on the client machine
    - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
    - [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
    - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
    - [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://mikefarah.gitbook.io/yq/#wget))
    - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
    - [kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/) - A command line tool to customize Kubernetes objects through a kustomization file.

1. set the environment variables - 

        export CLUSTER_NAME=<clustername>
        export CLUSTER_REGION=<clusterregion>
        export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

1. Created an EKS cluster
    - If you do not have an existing cluster, run the following command to create an EKS cluster. More details about cluster creation via `eksctl` can be found [here](https://eksctl.io/usage/creating-and-managing-clusters/).
    - Substitute values for the CLUSTER_NAME and CLUSTER_REGION in the script below
        ```
        eksctl create cluster \
        --name ${CLUSTER_NAME} \
        --version 1.19 \
        --region ${CLUSTER_REGION} \
        --nodegroup-name linux-nodes \
        --node-type m5.xlarge \
        --nodes 5 \
        --nodes-min 1 \
        --nodes-max 10 \
        --managed
        ```

1. AWS IAM permissions to create roles and attach policies to roles.

1. Clone the `awslabs/kubeflow-manifest` repo.

        git clone https://github.com/awslabs/kubeflow-manifests.git
        cd kubeflow-manifests
        git checkout v1.3-branch



## 1.0 Create the IAM Policy for the CSI Driver
Create an IAM policy that allows the CSI driver's service account to make calls to AWS APIs on your behalf.

a. Download the IAM policy document from GitHub as follows - 

```
curl -o iam-policy-example.json https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/v1.3.2/docs/iam-policy-example.json
```

b. Create the policy - 
```
aws iam create-policy \
    --policy-name AmazonEKS_EFS_CSI_Driver_Policy \
    --policy-document file://iam-policy-example.json
```

c. Create an IAM role and attach the IAM policy to it. Annotate the Kubernetes service account with the IAM role ARN and the IAM role with the Kubernetes service account name. You can create the role using eksctl as follows - 

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


## 2.0 Configure the EFS CSI Driver Image

In the file `distributions/aws/aws-efs-csi-driver/overlays/stable/ecr/kustomization.yaml` check the image region. If your cluster is not in the us-west-2 region, [replace the image URI with the correct URI for your region](https://docs.aws.amazon.com/eks/latest/userguide/add-ons-images.html). Once you've made the change, save your modified manifest.


## 3.0 Building manifests and deploying Kubeflow

Deploy Kubeflow using the following single line installation command -

```
while ! kustomize build examples/aws/storage-efs | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

This should have installed the EFS CSI Driver into the default kube-system namespace for you. You can check using the following command - 
```
kubectl get csidriver

NAME              ATTACHREQUIRED   PODINFOONMOUNT   MODES        AGE
efs.csi.aws.com   false            false            Persistent   5d17h
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

2. Determine the IP address of your cluster nodes.
```
kubectl get nodes
```

3. Determine the IDs of the subnets in your VPC and which Availability Zone the subnet is in.
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
    --subnet-id subnet-EXAMPLEe2ba886490
```


## 6.0 Using the EFS Storage in Kubeflow

### Sample 1 - Static Provisioning
[Using this sample from official AWS Docs](https://github.com/kubernetes-sigs/aws-efs-csi-driver/tree/master/examples/kubernetes/multiple_pods) we have provided the required spec files in the sample subdirectory but you can create the PVC another way. 

1. Use the `$file_system_id` you recorded before or use the following command to get the efs filesystem id - 
```
aws efs describe-file-systems --query "FileSystems[*].FileSystemId" --output text
```

2. Now edit the sample/pv.yaml and edit the `volumeHandle` to point to your EFS filesystem

3. Now create the required persistentvolume, persistentvolumeclaim and storageclass resources as -
```
kubectl apply -f examples/aws/storage-efs/sample/pv.yaml
kubectl apply -f examples/aws/storage-efs/sample/pvc.yaml
kubectl apply -f examples/aws/storage-efs/sample/sc.yaml
```


## 7.0 Connecting to Central dashboard
Port Forward as needed and Login to http://localhost:8080 using default credentials.

## 8.0 Test your Setup
Check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow as follows - 

### 8.1 Additional Permissions 
You might need to specify some additional directory permissions on your worker node before you can use these as mount points. The set-permission-job.yaml is an example of how you could set these permissions to be able to use the efs as your workspace in your kubeflow notebook. Edit the spec file as needed for your usecase
```
kubectl apply -f examples/aws/storage-efs/sample/set-permission-job.yaml
```

### 8.2 Using Kubeflow Notebooks
1. Spin up a new Kubeflow notebook server and specify the name of the PVC to be used as the workspace volume or the data volume and specify your desired mount point. 
2. In case the server does not start up in the expected time, do make sure to check - 
    - The Notebook Controller Logs
    - The specific notebook server instance pod's logs

### 8.3 Training using TFJob Operator
The following section re-uses the PVC and the Kubeflow Notebook created in the previous steps to download a dataset to the EFS Volume. Then we spin up a TFjob which runs a image classification job using the data from the shared volume. 
Source: https://www.tensorflow.org/tutorials/load_data/images

1. Download the dataset to the EFS Volume using the kubeflow notebook created above 
```
import pathlib
import tensorflow as tf
dataset_url = "https://storage.googleapis.com/download.tensorflow.org/example_images/flower_photos.tgz"
data_dir = tf.keras.utils.get_file(origin=dataset_url,
                                   fname='flower_photos',
                                   untar=True)
data_dir = pathlib.Path(data_dir)
```

2. Build and Push the Docker image 
```
cd examples/aws/storage-efs/training-sample
docker build -t <dockerimage:tag>
docker push <dockerimage:tag>
```

3. Create the TFjob and use the provided commands to check the training logs 
```
kubectl apply -f tfjob.yaml
kubectl describe tfjob image-classification-pvc -n kubeflow-user-example-com
kubectl logs -n kubeflow-user-example-com image-classification-pvc-worker-0 -f
```
