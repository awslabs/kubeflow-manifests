# Using Amazon EFS as Persistent Storage with Kubeflow

This guide describes how to use Amazon EFS as Persistent storage on top of an existing Kubeflow deployment.  

## 1.0 Prerequisites
1. For this README, we will assume that you already have an EKS Cluster with Kubeflow installed since the EFS CSI Driver can be installed and configured as a separate resource on top of an existing Kubeflow deployment. You can follow any of the other guides to complete these steps - choose one of the [AWS managed service integrated offering](../../README.md#deployment-options) or [generic distribution](../../vanilla/README.md).

**Important :**
You must make sure you have an [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) for your cluster and that it was added from `eksctl` >= `0.56` or if you already have an OIDC provider in place, then you must make sure you have the tag `alpha.eksctl.io/cluster-name` with the cluster name as its value. If you don't have the tag, you can add it via the AWS Console by navigating to IAM->Identity providers->Your OIDC->Tags.

2. At this point, you have likely cloned this repo and checked out the right branch. Navigate to the current directory - 
```
cd kubeflow-manifests/distributions/aws/examples/storage
```

3. Make sure the following environment variables are set. 
```
export CLUSTER_NAME=<clustername>
export CLUSTER_REGION=<clusterregion>
```

## 2.0 Setup EFS

You can either use Automated or Manual setup 

### 2.1 [Option 1] Automated setup
The script automates all the Manual steps and is only for Dynamic Provisioning option.  
It performs the required cluster configuration, creates an EFS file system and it also takes care of creating a storage class for dynamic provisioning.
1. Install the dependencies for the script
    1. Install the python dependencies `pip install -r requirements.txt`
    2. Install [eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html#installing-eksctl)
    3. Install [kubectl](https://kubernetes.io/docs/tasks/tools/)
2. Run the script
```
python auto-efs-setup.py --region $CLUSTER_REGION --cluster $CLUSTER_NAME
```
#### **Advanced customization**
The script applies some default values for the file system name, performance mode etc. If you know what you are doing, you can see which options are customizable by executing `python auto-efs-setup.py --help`.

### 2.1 [Option 2] Manual setup
If you prefer to manually setup each components then you can follow this manual guide.  

```
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
```

#### 1. Install the EFS CSI Driver
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

#### 2. Create the IAM Policy for the CSI Driver
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

#### 3. Manually Create an Instance of the EFS Filesystem
Please refer to the official [AWS EFS CSI Document](https://docs.aws.amazon.com/eks/latest/userguide/efs-csi.html#efs-create-filesystem) for detailed instructions on creating an EFS filesystem. 

Note: For this README, we have assumed that you are creating your EFS Filesystem in the same VPC as your EKS Cluster. 
  
#### Choose between dynamic and static provisioning  
In the following section, you have to choose between setting up [dynamic provisioning](https://kubernetes.io/docs/concepts/storage/dynamic-provisioning/) or setting up static provisioning.

#### 4. [Option 1] Dynamic Provisioning  
1. Use the `$file_system_id` you recorded in section 3 above or use the AWS Console to get the filesystem id of the EFS file system you want to use. Now edit the `dynamic-provisioning/sc.yaml` file by chaning `<YOUR_FILE_SYSTEM_ID>` with your `fs-xxxxxx` file system id. You can also change it using the following command :  
```
file_system_id=$file_system_id yq e '.parameters.fileSystemId = env(file_system_id)' -i dynamic-provisioning/sc.yaml
```  
  
2. Create the storage class using the following command :  
```
kubectl apply -f dynamic-provisioning/sc.yaml
```  
3. Verify your setup by checking which storage classes are created for your cluster. You can use the following command  
```
kubectl get sc
```  

Note : The `StorageClass` is a cluster scoped resource which means we only need to do this step once per cluster. 

#### 4. [Option 2] Static Provisioning
[Using this sample from official AWS Docs](https://github.com/kubernetes-sigs/aws-efs-csi-driver/tree/master/examples/kubernetes/multiple_pods) we have provided the required spec files in the sample subdirectory but you can create the PVC another way. 

1. Use the `$file_system_id` you recorded in section 3 above or use the AWS Console to get the filesystem id of the EFS file system you want to use. Now edit the last line of the static-provisioning/pv.yaml file to specify the `volumeHandle` field to point to your EFS filesystem. Replace `$file_system_id` if it is not already set. 
```
file_system_id=$file_system_id yq e '.spec.csi.volumeHandle = env(file_system_id)' -i static-provisioning/pv.yaml
```

2. The `PersistentVolume` and `StorageClass` are cluster scoped resources but the `PersistentVolumeClaim` needs to be in the namespace you will be accessing it from. Replace the `kubeflow-user-example-com` namespace specified the below with the namespace for your kubeflow user and edit the `static-provisioning/pvc.yaml` file accordingly. 
```
export PVC_NAMESPACE=kubeflow-user-example-com
yq e '.metadata.namespace = env(PVC_NAMESPACE)' -i static-provisioning/pvc.yaml
```

3. Now create the required persistentvolume, persistentvolumeclaim and storageclass resources as -
```
kubectl apply -f static-provisioning/sc.yaml
kubectl apply -f static-provisioning/pv.yaml
kubectl apply -f static-provisioning/pvc.yaml
```

4. Check your Setup
Use the following commands to ensure all resources have been deployed as expected and the PersistentVolume is correctly bound to the PersistentVolumeClaim
```
kubectl get pv

NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                 STORAGECLASS   REASON   AGE
efs-pv  5Gi        RWX            Retain           Bound    kubeflow-user-example-com/efs-claim   efs-sc                  5d16h
```

```
kubectl get pvc -n $PVC_NAMESPACE

NAME        STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
efs-claim   Bound    efs-pv   5Gi        RWX            efs-sc         5d16h
```

Now, Port Forward as needed and Login to the Kubeflow dashboard. You can also check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow. 
In the following two sections we will be using this PVC to create a notebook server with Amazon EFS mounted as the workspace volume, download training data into this filesystem and then deploy a TFJob to train a model using this data. 

## 3.0 Using EFS Storage in Kubeflow
### 3.1 Changing the default Storage Class
After installing Kubeflow, you can change the default Storage Class from `gp2` to the efs storage class you created during the setup. For instance, if you followed the automatic or manual steps, you should have a storage class named `efs-sc`. You can check your storage classes by running `kubectl get sc`.  
  
This is can be useful if your notebook configuration is set to use the default storage class (it is the case by default). By changing the default storage class, when creating workspace volumes for your notebooks, it will use your EFS storage class automatically. This is not mandatory as you can also manually create a PVC and select the `efs-sc` class via the Volume UI but can facilitate the notebook creation process and automatically select this class when creating volume in the UI. You can also decide to keep using `gp2` for workspace volumes and keep the EFS storage class for datasets/data volumes only.
  
To learn more about how to change the default Storage Class, you can refer to the [official Kubernetes documentation](https://kubernetes.io/docs/tasks/administer-cluster/change-default-storage-class/#changing-the-default-storageclass).  
  
For instance, if you have a default class set to `gp2` and another class `efs-sc`, then you would need to do the following : 
1. Remove `gp2` as your default storage class
```
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```
2. Set `efs-sc` as your default storage class
```
kubectl patch storageclass efs-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```
### 3.2 Creating and using EFS volumes as workspace or data volume for a notebook (Dynamic Provisioning)

**Important : The following example only works if you setup dynamic provisioning.**

Here is an example that illustrates how to create a PVC for your dataset in `ReadWriteMany` mode meaning it can be used by many notebooks at the same time as well as how to create a notebook with a workspace volume for the notebook data and how to specify that you want to use your dataset volume as data volume.
Note that both of these volumes are created under the storage class `efs-sc` which represents the EFS storage class created earlier.
  

https://user-images.githubusercontent.com/26939775/153103745-70f93ac5-88f3-4387-b40d-b585fca80af4.mp4


### 3.3 Using existing EFS volume as workspace or data volume for a notebook (Static Provisioning)

**Important : The following example only works if you setup static provisioning.**

Spin up a new Kubeflow notebook server and specify the name of the PVC to be used as the workspace volume or the data volume and specify your desired mount point. We'll assume you created a PVC with the name `efs-claim` via Kubeflow Volumes UI or via the manual setup step [Static Provisioning](./README.md#4-static-provisioning). For our example here, we are using the AWS Optimized Tensorflow 2.6 CPU image provided in the notebook configuration options - `public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow`. Additionally, use the existing `efs-claim` volume as the workspace volume at the default mount point `/home/jovyan`. The server might take a few minutes to come up. 

In case the server does not start up in the expected time, do make sure to check - 
1. The Notebook Controller Logs
2. The specific notebook server instance pod's logs

### Note about Permissions
You might need to specify some additional directory permissions on your worker node before you can use these as mount points. By default, new Amazon EFS file systems are owned by root:root, and only the root user (UID 0) has read-write-execute permissions. If your containers are not running as root, you must change the Amazon EFS file system permissions to allow other users to modify the file system. The set-permission-job.yaml is an example of how you could set these permissions to be able to use the efs as your workspace in your kubeflow notebook. 

```
export CLAIM_NAME=efs-claim
yq e '.metadata.name = env(CLAIM_NAME)' -i notebook-sample/set-permission-job.yaml
yq e '.metadata.namespace = env(PVC_NAMESPACE)' -i notebook-sample/set-permission-job.yaml
yq e '.spec.template.spec.volumes[0].persistentVolumeClaim.claimName = env(CLAIM_NAME)' -i notebook-sample/set-permission-job.yaml

kubectl apply -f notebook-sample/set-permission-job.yaml
```

### 3.4 Using EFS volume for a TrainingJob using TFJob Operator
The following section re-uses the PVC and the Tensorflow Kubeflow Notebook created in the previous steps to download a dataset to the EFS Volume. Then we spin up a TFjob which runs a image classification job using the data from the shared volume. 
Source: https://www.tensorflow.org/tutorials/load_data/images

Note: The following steps are run from the terminal on your gateway node connected to your EKS cluster and not from the Kubeflow Notebook to test the PVC allowed sharing of data as expected. 

#### 1. Download the dataset to the EFS Volume 
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

#### 2. Build and Push the Docker image
In the `training-sample` directory, we have provided a sample training script and Dockerfile which you can use as follows to build a docker image. Be sure to point the `$IMAGE_URI` to your registry and specify an appropriate tag - 
```
export IMAGE_URI=<dockerimage:tag>
cd training-sample

# You will need to login to ECR for the following steps
docker build -t $IMAGE_URI .
docker push $IMAGE_URI
cd -
```

#### 3. Configure the tfjob spec file
Once the docker image is built, replace the `<dockerimage:tag>` in the `tfjob.yaml` file, line #17. 
```
yq e '.spec.tfReplicaSpecs.Worker.template.spec.containers[0].image = env(IMAGE_URI)' -i training-sample/tfjob.yaml
```
Also, specify the name of the PVC you created - 
```
export CLAIM_NAME=efs-claim
yq e '.spec.tfReplicaSpecs.Worker.template.spec.volumes[0].persistentVolumeClaim.claimName = env(CLAIM_NAME)' -i training-sample/tfjob.yaml
```
Make sure to run it in the same namespace as the claim - 
```
yq e '.metadata.namespace = env(PVC_NAMESPACE)' -i training-sample/tfjob.yaml
```

#### 4. Create the TFjob and use the provided commands to check the training logs 
At this point, we are ready to train the model using the `training-sample/training.py` script and the data available on the shared volume with the Kubeflow TFJob operator as -
```
kubectl apply -f training-sample/tfjob.yaml
```

In order to check that the training job is running as expected, you can check the events in the TFJob describe response as well as the job logs as - 
```
kubectl describe tfjob image-classification-pvc -n $PVC_NAMESPACE
kubectl logs -n $PVC_NAMESPACE image-classification-pvc-worker-0 -f
```

## 4.0 Cleanup
This section cleans up the resources created in this README, to cleanup other resources such as the Kubeflow deployment, please refer to the high level README files. 

### 4.1 Clean up the TFJob
```
kubectl delete tfjob -n $PVC_NAMESPACE image-classification-pvc
```

### 4.2 Delete the Kubeflow Notebook
Login to the dashboard to stop and/or terminate any kubeflow notebooks you created for this session or use the following command - 
```
kubectl delete notebook -n $PVC_NAMESPACE <notebook-name>
``` 
Use the following command to delete the permissions job - 
```
kubectl delete pod -n $PVC_NAMESPACE $CLAIM_NAME
```

### 4.3 Delete PVC, PV and SC in the following order
```
kubectl delete pvc -n $PVC_NAMESPACE $CLAIM_NAME
kubectl delete pv efs-pv
kubectl delete sc efs-sc
```

### 4.4 Delete the EFS mount targets, filesystem and security group
Use the steps in this [AWS Guide](https://docs.aws.amazon.com/efs/latest/ug/delete-efs-fs.html) to delete the EFS filesystem that you created.
