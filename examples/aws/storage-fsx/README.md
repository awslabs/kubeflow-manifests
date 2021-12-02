# Deploying Kubeflow with Amazon FSx for Lustre as Persistent Storage

This guide describes how to deploy Kubeflow on AWS EKS using Amazon FSx for Lustre as the Persistent Storage.

## Prerequisites

## 1. Prerequisites
Follow the pre-requisites section from [this guide](../rds-s3/README.md#1-prerequisites) to:
1. Install the CLI tools
2. Clone the repo and checkout the right branch
3. Create an EKS cluster and
4. Make sure the following environment variables are set - 
```
export CLUSTER_NAME=<clustername>
export CLUSTER_REGION=<clusterregion>
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
```

## 1.0 Create the IAM Policy for the CSI Driver
Create an IAM policy that allows the CSI driver's service account to make calls to AWS APIs on your behalf.

a. Create the policy using the json file provided as follows - 
```
aws iam create-policy \
    --policy-name Amazon_FSx_Lustre_CSI_Driver \
    --policy-document file://examples/aws/storage-fsx/fsx-csi-driver.json
```

b. Create an IAM role and attach the IAM policy to it. Annotate the Kubernetes service account with the IAM role ARN and the IAM role with the Kubernetes service account name. You can create the role using eksctl as follows - 

```
eksctl create iamserviceaccount \
    --name fsx-csi-controller-sa \
    --namespace kube-system \
    --cluster $CLUSTER_NAME \
    --attach-policy-arn arn:aws:iam::$AWS_ACCOUNT_ID:policy/Amazon_FSx_Lustre_CSI_Driver \
    --region $CLUSTER_REGION \
    --approve \
    --override-existing-serviceaccounts 
```


## 2.0 Configure the Service Account 

a. In your AWS Console, go to the CloudFormation Service. Find the stack named `eksctl-prod-addon-iamserviceaccount-kube-system-fsx-csi-controller-sa` and check the outputs tab to find the name of the RoleARN that was created.

b. Now, in the file `distributions/aws/aws-fsx-csi-driver/base/controller-serviceaccount.yaml`, edit line #9 to add the role created in the previous step. 


## 3.0 Building manifests and deploying Kubeflow

a. Deploy Kubeflow using the following single line installation command -

```
while ! kustomize build examples/aws/storage-fsx | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

b. This should have installed the FSx CSI Driver into the default kube-system namespace for you. You can check using the following command - 
```
kubectl get csidriver -A

NAME              ATTACHREQUIRED   PODINFOONMOUNT   MODES        AGE
fsx.csi.aws.com   false            false            Persistent   5d17h
```

## 4.0 Create an Instance of the FSx Filesystem
This section creates a new FSx volume using for your cluster. Please refer to the official [AWS Documents](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html) for more details. 

1. Retrieve the VPC ID that your cluster is in and store it in a variable for use in a later step.
```
vpc_id=$(aws eks describe-cluster \
    --name $CLUSTER_NAME\
    --query "cluster.resourcesVpcConfig.vpcId" \
    --output text)
```

2. Get the Cluster's security group
```
cluster_security_group=$(aws eks describe-cluster \
--name $CLUSTER_NAME \
--query cluster.resourcesVpcConfig.clusterSecurityGroupId)
```

3. Determine the IDs of the subnets in your VPC and which Availability Zone the subnet is in. Use one public subet while creating the filesystem
```
subnet_id=$(aws eks describe-cluster --name $CLUSTER_NAME --query "cluster.resourcesVpcConfig.subnetIds[0]" --output text)
```

3. Create a security group with an inbound rule that allows inbound Lustre traffic for your Amazon FSx mount points.
    a. Create a security group. 
    ```
    security_group_id=$(aws ec2 create-security-group \
        --group-name MyFSxSecurityGroup \
        --description "My FSx security group" \
        --vpc-id $vpc_id \
        --output text)
    ```

    b. Create an inbound rule that allows inbound NFS traffic from the CIDR for your cluster's VPC.
    ```
    aws ec2 authorize-security-group-ingress \
        --group-id $security_group_id \
        --protocol tcp \
        --port 988 \
        --source-group $security_group_id
    ```

    ```
    aws ec2 authorize-security-group-ingress \
        --group-id $security_group_id \
        --protocol tcp \
        --port 988 \
        --source-group $cluster_security_group
    ```

4. Create an Amazon FSx for Lustre file system for your Amazon EKS cluster.
```
file_system_id=$(aws fsx create-file-system \
    --region $CLUSTER_REGION \
    --file-system-type LUSTRE \
    --storage-capacity 1200 \
    --subnet-ids "$subnet_id" \
    --security-group-ids "$security_group_id" \
    --query 'FileSystem.FileSystemId' \
    --output text)
```

## 6.0 Using the Amazon FSx Storage in Kubeflow

### Sample 1 - Static Provisioning
[Using this sample from official Kubeflow Docs](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/storage/#amazon-fsx-for-lustre) 

1. Use the following command to retrieve the FileSystemId, DNSName, and MountName values.
```
aws fsx describe-file-systems --file-system-ids $file_system_id
```

2. Now edit the sample/fsx-pv.yaml to replace <file_system_id>, <dns_name>, and <mount_name> with your values and create it with kubectl
```
kubectl apply -f examples/aws/storage-fsx/sample/fsx-pv.yaml
```

3. Now you can create a claim on the volume for use as - 
```
kubectl apply -f examples/aws/storage-fsx/sample/fsx-pvc.yaml
```
## 7.0 Connecting to Central dashboard
Port Forward as needed and Login to http://localhost:8080 using default credentials.

## 8.0 Test your Setup
Check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow as follows - 

### 8.1 Additional Permissions 
You might need to specify some additional directory permissions on your worker node before you can use these as mount points. The set-permission-job.yaml is an example of how you could set these permissions to be able to use the fsx-claim as your data-volume in your kubeflow notebook. Edit the spec file as needed for your usecase
```
kubectl apply -f examples/aws/storage-fsx/sample/set-permission-job.yaml
```
### 8.2 Using Kubeflow Notebooks
1. Spin up a new Kubeflow notebook server and specify the name of the PVC to be used as the the data volume and specify your desired mount point. 
2. In case the server does not start up in the expected time, do make sure to check - 
    - The Notebook Controller Logs
    - The specific notebook server instance pod's logs
3. You should be able to monitor usage via the Amazon FSx Service on the AWS Console.
