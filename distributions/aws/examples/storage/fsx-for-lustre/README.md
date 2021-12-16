# Using Amazon FSx as Persistent Storage with Kubeflow

This guide describes how to use Amazon FSx as Persistent storage on top of an existing Kubeflow deployment.  

## 1.0 Prerequisites
1. For this README, we will assume that you already have an EKS Cluster with Kubeflow installed since the FSx CSI Driver can be installed and configured as a separate resource on top of an existing Kubeflow deployment. You can follow any of the other guides to complete these steps - choose one of the [AWS managed service integrated offering](../../README.md) or [generic distribution](../../../../../README.md).

2. At this point, you have likely cloned this repo and checked out the right branch. All paths in the following steps are relative to `kubeflow-manifests/distributions/aws/examples/storage` directory.

3. Make sure the following environment variables are set. 
```
export CLUSTER_NAME=<clustername>
export CLUSTER_REGION=<clusterregion>
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
```

## 2.0 Install the FSx CSI Driver
We recommend installing the FSx CSI Driver v1.3.4 directly from the [the aws-fsx-csi-driver github repo](https://github.com/kubernetes-sigs/aws-fsx-csi-driver) as follows - 

```
kubectl apply -k "github.com/kubernetes-sigs/aws-fsx-csi-driver/deploy/kubernetes/overlays/stable/?ref=tags/v0.7.1"
```

You can confirm that FSx CSI Driver was installed using the following command - 
```
kubectl get csidriver -A

NAME              ATTACHREQUIRED   PODINFOONMOUNT   MODES        AGE
fsx.csi.aws.com   false            false            Persistent   14s
```

## 3.0 Create the IAM Policy for the CSI Driver
The CSI driver's service account (created during installation) requires IAM permission to make calls to AWS APIs on your behalf. Here, we will be annotating the Service Account `fsx-csi-controller-sa` with an IAM Role which has the required permissions.

1. Create the policy using the json file provided as follows - 
```
aws iam create-policy \
    --policy-name Amazon_FSx_Lustre_CSI_Driver \
    --policy-document file://fsx-for-lustre/fsx-csi-driver.json
```

2. Create an IAM role and attach the IAM policy to it. Annotate the Kubernetes service account with the IAM role ARN and the IAM role with the Kubernetes service account name. You can create the role using eksctl as follows - 

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

3. You can verify by describing the specified service account to check if it has been correctly annotated - 
```
kubectl describe -n kube-system serviceaccount fsx-csi-controller-sa
```

## 4.0 Create an Instance of the FSx Filesystem
Please refer to the official [AWS FSx CSI Document](https://docs.aws.amazon.com/eks/latest/userguide/fsx-csi.html) for detailed instructions on creating an FSx filesystem. 

## 5.0 Using FSx Storage in Kubeflow

## 5.1 Provisioning Options
### Option 1 - Static Provisioning
[Using this sample from official Kubeflow Docs](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/storage/#amazon-fsx-for-lustre) 

1. Use the AWS Console to get the filesystem id of the FSx volume you want to use. You could also use the following command to list all the volumes available in your region. Either way, make sure that `file_system_id` is set. 
```
aws fsx describe-file-systems --query "FileSystems[*].FileSystemId" --output text --region $CLUSTER_REGION
```

```
export file_system_id=<fsx-id-to-use>
```

2. Once you have the filesystem id, Use the following command to retriev DNSName, and MountName values.
```
export dns_name=$(aws fsx describe-file-systems --file-system-ids $file_system_id --query "FileSystems[0].DNSName" --output text --region $CLUSTER_REGION)

export mount_name=$(aws fsx describe-file-systems --file-system-ids $file_system_id --query "FileSystems[0].LustreConfiguration.MountName" --output text --region $CLUSTER_REGION)
```

3. Now edit the sample/fsx-pv.yaml to replace <file_system_id>, <dns_name>, and <mount_name> with your values.
```
yq e '.spec.csi.volumeHandle = env(file_system_id)' -i fsx-for-lustre/static-provisioning/fsx-pv.yaml
yq e '.spec.csi.volumeAttributes.dnsname = env(dns_name)' -i fsx-for-lustre/static-provisioning/fsx-pv.yaml
yq e '.spec.csi.volumeAttributes.mountname = env(mount_name)' -i fsx-for-lustre/static-provisioning/fsx-pv.yaml
```

4. The `PersistentVolume` is a cluster scoped resource but the `PersistentVolumeClaim` needs to be in the namespace you will be accessing it from. Be sure to replace the `kubeflow-user-example-com` namespace specified in the `fsx-for-lustre/static-provisioning/fsx-pvc.yaml` file with the namespace for the kubeflow user. 

5. Now create the required persistentvolume and persistentvolumeclaim resources as -
```
kubectl apply -f fsx-for-lustre/static-provisioning/fsx-pv.yaml
kubectl apply -f fsx-for-lustre/static-provisioning/fsx-pvc.yaml
```

## 5.2 Check your Setup
Use the following commands to ensure all resources have been deployed as expected and the PersistentVolume is correctly bound to the PersistentVolumeClaim
```
kubectl get pv

NAME    CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                 STORAGECLASS   REASON   AGE
fsx-pv  1200Gi     RWX            Recycle          Bound    kubeflow-user-example-com/fsx-claim                           11s
```

```
kubectl get pvc -n kubeflow-user-example-com

NAME        STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
fsx-claim   Bound    fsx-pv   1200Gi     RWX                           83s
```

Now, Port Forward as needed and Login to the Kubeflow dashboard. You can also check the `Volumes` tab in Kubeflow and you should be able to see your PVC is available for use within Kubeflow. 
In the following two sections we will be using this PVC to create a notebook server with Amazon FSx mounted as the workspace volume, download training data into this filesystem and then deploy a TFJob to train a model using this data. 

## 5.3 Using FSx volume as workspace or data volume for a notebook server 

Spin up a new Kubeflow notebook server and specify the name of the PVC to be used as the workspace volume or the data volume and specify your desired mount point. For our example here, we are using the `AWS Optimized Tensorflow 2.6 CPU image` provided in the notebook configuration options. Additionally, use the existing `fsx-claim` volume as the workspace volume at the default mount point `/home/jovyan`. The server might take a few minutes to come up. 

In case the server does not start up in the expected time, do make sure to check - 
1. The Notebook Controller Logs
2. The specific notebook server instance pod's logs

### Note about Permissions
You might need to specify some additional directory permissions on your worker node before you can use these as mount points. By default, new Amazon FSx file systems are owned by root:root, and only the root user (UID 0) has read-write-execute permissions. If your containers are not running as root, you must change the Amazon FSx file system permissions to allow other users to modify the file system. The set-permission-job.yaml is an example of how you could set these permissions to be able to use the FSx as your workspace in your kubeflow notebook. 
```
kubectl apply -f fsx-for-lustre/static-provisioning/set-permission-job.yaml
```
If you use FSx for other purposes (e.g. sharing data across pipelines), you don’t need this step.

## 5.4 Using FSx volume for a TrainingJob using TFJob Operator
The following section re-uses the PVC and the Tensorflow Kubeflow Notebook created in the previous steps to download a dataset to the FSx Volume. Then we spin up a TFjob which runs a image classification job using the data from the shared volume. 
Source: https://www.tensorflow.org/tutorials/load_data/images

### 1. Download the dataset to the FSx Volume 
In the Kubeflow Notebook created above, use the following snippet to download the data into the `/home/jovyan/.keras` directory (which is mounted onto the FSx Volume). 
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
In the `training-sample` directory, we have provided a sample training script and Dockerfile which you can use as follows to build a docker image. Be sure to point the `$IMAGE_URI` to your registry and specify an appropriate tag - 
```
export IMAGE_URI=<dockerimage:tag>
cd training-sample

# You will need to login to ECR for the following steps
docker build -t $IMAGE_URI .
docker push $IMAGE_URI
cd -
```

### 3. Configure the tfjob spec file
Once the docker image is built, replace the `<dockerimage:tag>` in the `tfjob.yaml` file, line #17. 
```
yq e '.spec.tfReplicaSpecs.Worker.template.spec.containers[0].image = env(IMAGE_URI)' -i training-sample/tfjob.yaml
```
Also, specify the name of the PVC you created - 
```
export CLAIM_NAME=fsx-claim
yq e '.spec.tfReplicaSpecs.Worker.template.spec.volumes[0].persistentVolumeClaim.claimName = env(CLAIM_NAME)' -i training-sample/tfjob.yaml
```

### 3. Create the TFjob and use the provided commands to check the training logs 
At this point, we are ready to train the model using the `training-sample/training.py` script and the data available on the shared volume with the Kubeflow TFJob operator as -
```
kubectl apply -f training-sample/tfjob.yaml
```

In order to check that the training job is running as expected, you can check the events in the TFJob describe response as well as the job logs as - 
```
kubectl describe tfjob image-classification-pvc -n kubeflow-user-example-com
kubectl logs -n kubeflow-user-example-com image-classification-pvc-worker-0 -f
```
