# Kustomize Manifests for RDS and S3

## Overview

This Kustomize Manifest can be used to deploy Kubeflow Pipelines and Katib with RDS and S3.

### RDS

[Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) is a managed relational database service that facilitates several database management tasks such as database scaling, database backups, database software patching, OS patching, and more.

In the [default kubeflow installation](../../../../example/kustomization.yaml), the [KFP](../../../../apps/katib/upstream/components/mysql/mysql.yaml) and [Katib](../../../../apps/pipeline/upstream/third-party/mysql/base/mysql-deployment.yaml) components both use their own MySQL pod to persist KFP data (such as experiments, pipelines, jobs, etc.) and Katib experiment observation logs, respectively. 

As compared to using the MySQL setup in the default installation, using RDS provides the following advantages:
- Easier to configure scalability and availability: RDS provides high availability and failover support for DB instances using Multi-AZ deployments with a single standby DB instance, increasing the availability of KFP and Katib services during unexpected network events.
- Persisted KFP and Katib data can be reused across Kubeflow versions: Using RDS decouples the KFP and Katib datastores from the Kubeflow deployment, allowing the same RDS instance to be used across multiple Kubeflow deployments and versions.
- Higher level of customizability and management: RDS provides management features to facilitate changing database instance types, updating SQL versions, and more.


### S3
[Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide//Welcome.html) is an object storage service that is highly scalable, available, secure, and performant. 

In the [default kubeflow installation](../../../../example/kustomization.yaml), the [KFP](../../../../apps/pipeline/upstream/third-party/minio/base/minio-deployment.yaml) component uses the MinIO object storage service that can be configured to store objects in S3. However, by default the installation hosts the object store service locally in the cluster. KFP stores data such as pipeline architectures and pipeline run artifacts in MinIO.

Configuring MinIO to read and write to S3 provides the following advantages:
- Higher scalability and availability: S3 offers industry-leading scalability and availability and is more durable than the default MinIO object storage solution provided by Kubeflow.
- Persisted KFP data can be reused across Kubeflow version: Using S3 decouples the KFP object datastore from the Kubeflow deployment, allowing the same S3 resources to be used across multiple Kubeflow deployments and versions.
- Higher level of customizability and management: S3 provides management features to help optimize, organize, and configure access to your data to meet your specific business, organizational, and compliance requirements

To get started with configuring and installing your Kubeflow installation with RDS and S3 follow the [install](#install) steps below to configure and deploy the Kustomize manifest.

## Install

Similar to [the single command base installation](../../../../README.md#install-with-a-single-command) the AWS install configures the Kubeflow official components to integrate with supported AWS services.

The following steps show how to configure and deploy:

## 1.0 Prerequisites

1. Install CLI tools

   - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
   - [eksctl >= 0.56](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
   - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
   - [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://mikefarah.gitbook.io/yq/#wget))
   - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
   - [kustomize version 3.2.0](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0) - A command line tool to customize Kubernetes objects through a kustomization file.
     - :warning: Kubeflow 1.3.0 is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.


2. Clone the repo and checkout the release branch

```
git clone https://github.com/awslabs/kubeflow-manifests.git
cd kubeflow-manifests
git checkout v1.3-branch
```

3. Create an EKS cluster

Run this command to create an EKS cluster by changing `<YOUR_CLUSTER_NAME>` and `<YOUR_CLUSTER_REGION>` to your preferred settings. More details about cluster creation via `eksctl` can be found [here](https://eksctl.io/usage/creating-and-managing-clusters/).

```
export CLUSTER_NAME=<YOUR_CLUSTER_NAME>
export CLUSTER_REGION=<YOUR_CLUSTER_REGION>

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

4. Create an OIDC provider for your cluster  
**Important :**  
You must make sure you have an [OIDC provider](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html) for your cluster and that it was added from `eksctl` >= `0.56` or if you already have an OIDC provider in place, then you must make sure you have the tag `alpha.eksctl.io/cluster-name` with the cluster name as its value. If you don't have the tag, you can add it via the AWS Console by navigating to IAM->Identity providers->Your OIDC->Tags.

## 2.0 Setup RDS, S3 and configure Secrets
To facilitate creating the RDS and S3 resources an automated python script has been provided. 

:warning The automated python script setups an environment to be used for development/testing purposes. To help setup an environment that meets your production needs, please refer to the [RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) and [S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide//Welcome.html) documentation. 

The script takes care of creating the S3 bucket, creating the S3 secrets using the secrets manager, setting up the RDS database and creating the RDS secret using the secrets manager. It also edits the required configuration files for Kubeflow pipeline to be properly configured for the RDS database during Kubeflow installation.  
The script also handles cases where the resources already exist in which case it will simply skips the step.
  
Note : The script will **not** delete any resource therefore if a secret already exist or if a database with the same name already exist or if the S3 bucket already exists for instance, it will skip those steps. This was done in order to prevent unwanted results such as accidental deletion. For instance, if a database with the same name already exists, the script will skip the database creation setup. If it's expected in your scenario, then perhaps this is fine for you, if you simply forgot to change the database name used for creation then this gives you the chance to retry the script with the proper value. See `python auto-rds-s3-setup.py --help` for the list of parameters as well as their default values.

1. Install the dependencies for the script
    1. Install the python dependencies `pip install -r requirements.txt`
    2. Install [eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html#installing-eksctl)
    3. Install [kubectl](https://kubernetes.io/docs/tasks/tools/)
2. Run the script  
Replace `YOUR_CLUSTER_REGION`, `YOUR_CLUSTER_NAME` and `YOUR_S3_BUCKET` with your values.
```
python auto-rds-s3-setup.py --region YOUR_CLUSTER_REGION --cluster YOUR_CLUSTER_NAME --bucket YOUR_S3_BUCKET
```  

### Advanced customization
The script applies some sensible default values for the db user password, max storage, storage type, instance type etc but if you know what you are doing, you can always tweak those preferences by passing different values.  
You can learn more about the different parameters by running `python auto-rds-s3-setup.py --help`.  

3. Create Secrets in AWS Secrets Manager

   1. Configure a secret named `rds-secret` with the RDS DB name, RDS endpoint URL, RDS DB port, and RDS DB credentials that were configured when following the steps in Create RDS Instance.
      - For example, if your database name is `kubeflow`, your endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, your DB port is `3306`, your DB username is `admin`, and your DB password is `Kubefl0w` your secret should look like:
      - **Note:** These are the default values for the database name and credentials in cloudformation template for creating the RDS instance, change these according to the values you used
      - ```
        aws secretsmanager create-secret --name rds-secret --secret-string '{"username":"admin","password":"Kubefl0w","database":"kubeflow","host":"rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com","port":"3306"}' --region $CLUSTER_REGION
        ```
   1. Configure a secret named `s3-secret` with your AWS credentials. These need to be long term credentials from an IAM user and not temporary.
      - Find more details about configuring/getting your AWS credentials here:
        https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html
      - ```
        aws secretsmanager create-secret --name s3-secret --secret-string '{"accesskey":"AXXXXXXXXXXXXXXXXXX6","secretkey":"eXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXq"}' --region $CLUSTER_REGION
        ```

4. Install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver

   1. Run the following commands to enable oidc and create an iamserviceaccount with permissions to retrieve the secrets created from AWS Secrets Manager

   ```
   eksctl utils associate-iam-oidc-provider --region=$CLUSTER_REGION --cluster=$CLUSTER_NAME --approve

   eksctl create iamserviceaccount  --name kubeflow-secrets-manager-sa  --namespace kubeflow  --cluster $CLUSTER_NAME --attach-policy-arn  arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite --override-existing-serviceaccounts   --approve --region $CLUSTER_REGION
   ```

   2. Run these commands to install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver

   ```
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretproviderclass.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/csidriver.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store-csi-driver.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretprovidersyncing.yaml

    kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
   ```

5. Configure Kubeflow Pipelines by editing the following file in `apps/pipeline/upstream/env/aws` directory:

   1. Configure `apps/pipeline/upstream/env/aws/params.env` file with the RDS endpoint URL, S3 bucket name, and S3 bucket region that were configured when following the steps in Create RDS Instance and Create S3 Bucket steps in prerequisites(#1-prerequisites).

      - For example, if your RDS endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, S3 bucket name is `kf-aws-demo-bucket`, and s3 bucket region is `us-west-2` your `params.env` file should look like:
      - ```
        dbHost=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com

        bucketName=kf-aws-demo-bucket
        minioServiceHost=s3.amazonaws.com
        minioServiceRegion=us-west-2
        ```

## 3.0 Build Manifests and Install Kubeflow
Once you have the resources ready, you can continue on to deploying the Kubeflow manifests using the single line command below -

```sh
while ! kustomize build distributions/aws/examples/rds-s3 | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

After everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster](../../../../README.md#connect-to-your-kubeflow-cluster).

Congratulations! You can now start experimenting and running your end-to-end ML workflows with Kubeflow.

## 4.0 Verify the installation

### 4.1 Verify RDS

1. Connect to the RDS instance from a pod within the cluster

```
kubectl run -it --rm --image=mysql:5.7 --restart=Never mysql-client -- mysql -h <YOUR RDS ENDPOINT> -u <YOUR LOGIN> -p<YOUR PASSWORD>
```

If you used the default parameters in the [CFN template](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/files/rds.yaml) given at step 5 of the Prerequistes, the command would look like

```
kubectl run -it --rm --image=mysql:5.7 --restart=Never mysql-client -- mysql -h <YOUR RDS ENDPOINT> -u admin -pKubefl0w
```

Note that you can find your credentials by visiting [aws secrets manager](https://aws.amazon.com/secrets-manager/) or by using [AWS CLI](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/secretsmanager/get-secret-value.html)  

For instance, to retrieve the value of a secret named `rds-secret`, we would do : 
```
aws secretsmanager get-secret-value \
    --region $CLUSTER_REGION \
    --secret-id rds-secret \
    --query 'SecretString' \
    --output text
```

2. Once connected verify the databases `kubeflow` and `mlpipeline` exist.

```
mysql> show databases;

+--------------------+
| Database           |
+--------------------+
| information_schema |
| kubeflow           |
| mlpipeline         |
| mysql              |
| performance_schema |
+--------------------+
```

3. Verify the database `mlpipeline` has the following tables:

```
mysql> use mlpipeline; show tables;

+----------------------+
| Tables_in_mlpipeline |
+----------------------+
| db_statuses          |
| default_experiments  |
| experiments          |
| jobs                 |
| pipeline_versions    |
| pipelines            |
| resource_references  |
| run_details          |
| run_metrics          |
+----------------------+
```

4. Access the Kubeflow Central Dashboard [by logging in to your cluster](../../../../README.md#connect-to-your-kubeflow-cluster) and navigate to Katib (under Experiments (AutoML)).

5. Create an experiment using the following [yaml file](../../test/e2e/resources/custom-resource-templates/katib-experiment-random.yaml).

6. Once the experiment is complete verify the following table exists:

```
mysql> use kubeflow; show tables;

+----------------------+
| Tables_in_kubeflow   |
+----------------------+
| observation_logs     |
+----------------------+
```

7. Describe `observation_logs` to verify it is being populated.

```
mysql> select * from observation_logs;
```

### 4.2 Verify S3

1. Access the Kubeflow Central Dashboard [by logging in to your cluster](../../../../README.md#connect-to-your-kubeflow-cluster) and navigate to Kubeflow Pipelines (under Pipelines).

2. Create an experiment named `test` and create a run using the sample pipeline `[Demo] XGBoost - Iterative model training`.

3. Once the run is completed go to the S3 AWS console and open the bucket you specified for the Kubeflow installation.

4. Verify the bucket is not empty and was populated by outputs of the experiment.

## 5.0 Uninstall Kubeflow

Run the following command to uninstall:

```sh
kustomize build distributions/aws/examples/rds-s3 | kubectl delete -f -
```

Additionally, the following cleanup steps may be required:

```sh
kubectl delete mutatingwebhookconfigurations.admissionregistration.k8s.io webhook.eventing.knative.dev webhook.istio.networking.internal.knative.dev webhook.serving.knative.dev

kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io config.webhook.eventing.knative.dev config.webhook.istio.networking.internal.knative.dev config.webhook.serving.knative.dev

kubectl delete endpoints -n default mxnet-operator pytorch-operator tf-operator
```
