# Kustomize Manifests for RDS and S3

## Overview

This Kustomize Manifest can be used to deploy Kubeflow Pipelines (KFP) and Katib with RDS and S3.

### RDS

[Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) is a managed relational database service that facilitates several database management tasks such as database scaling, database backups, database software patching, OS patching, and more.

In the [default kubeflow installation](../../../../example/kustomization.yaml), the [KFP](../../../../apps/katib/upstream/components/mysql/mysql.yaml) and [Katib](../../../../apps/pipeline/upstream/third-party/mysql/base/mysql-deployment.yaml) components both use their own MySQL pod to persist KFP data (such as experiments, pipelines, jobs, etc.) and Katib experiment observation logs, respectively. 

As compared to using the MySQL setup in the default installation, using RDS provides the following advantages:
- Easier to configure scalability and availability: RDS provides high availability and failover support for DB instances using Multi-AZ deployments with a single standby DB instance, increasing the availability of KFP and Katib services during unexpected network events.
- Persisted KFP and Katib data can be reused across Kubeflow installations with the same Kubeflow version: Using RDS decouples the KFP and Katib datastores from the Kubeflow deployment, allowing the same RDS instance to be used across multiple Kubeflow installations with the same Kubeflow version.
- Higher level of customizability and management: RDS provides management features to facilitate changing database instance types, updating SQL versions, and more.

### S3
[Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) is an object storage service that is highly scalable, available, secure, and performant. 

In the [default kubeflow installation](../../../../example/kustomization.yaml), the [KFP](../../../../apps/pipeline/upstream/third-party/minio/base/minio-deployment.yaml) component uses the MinIO object storage service that can be configured to store objects in S3. However, by default the installation hosts the object store service locally in the cluster. KFP stores data such as pipeline architectures and pipeline run artifacts in MinIO.

Configuring MinIO to read and write to S3 provides the following advantages:
- Higher scalability and availability: S3 offers industry-leading scalability and availability and is more durable than the default MinIO object storage solution provided by Kubeflow.
- Persisted KFP metadata can be reused across Kubeflow installations with same Kubeflow version: Using S3 decouples the KFP object datastore from the Kubeflow deployment, allowing the same S3 resources to be used across multiple Kubeflow installations with the same Kubeflow version.
- Higher level of customizability and management: S3 provides management features to help optimize, organize, and configure access to your data to meet your specific business, organizational, and compliance requirements

To get started with configuring and installing your Kubeflow installation with RDS and S3 follow the [install](#install) steps below to configure and deploy the Kustomize manifest.

## Install

The following steps show how to configure and deploy Kubeflow with supported AWS services.

### Using only RDS or only S3

Steps relevant only to the RDS installation will be prefixed with `[RDS]`.
Steps relevant only to the S3 installation will be prefixed with `[S3]`.
Steps without any prefixing are necessary for all installations.

To install for either only RDS or S3 complete the steps relevant to your installation choice.

## 1.0 Prerequisites

1. Install CLI tools

   - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
   - [eksctl >= 0.56](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
   - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
   - [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://github.com/mikefarah/yq/#install))
   - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
   - [kustomize version 3.2.0](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0) - A command line tool to customize Kubernetes objects through a kustomization file.
     - :warning: Kubeflow is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.

1. Clone the `awslabs/kubeflow-manifest` repo, `kubeflow/manifests` repo and checkout the release branches.

   - Substitute the value for `KUBEFLOW_RELEASE_VERSION`(e.g. v1.4.1) and `AWS_RELEASE_VERSION`(e.g. v1.4.1-aws-b1.0.0) with the tag or branch you want to use below. Read more about [releases and versioning](../../community/releases.md#releases-and-versioning) policy if you are unsure about what these values should be.
     ```
     export KUBEFLOW_RELEASE_VERSION=<>
     export AWS_RELEASE_VERSION=<>
     git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests
     git checkout ${AWS_RELEASE_VERSION}
     git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream
     ```

1. Create an EKS cluster

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

There are two ways to create the RDS and S3 resources before you deploy the Kubeflow manifests. Either use the automated python script we have provided by following the steps in section 2.1 or fall back on the manual setup steps as in section 2.2 below -

### 2.1 **Option 1: Automated Setup**

This setup performs all the manual steps in an automated fashion.  
The script takes care of creating the S3 bucket, creating the S3 secrets using the secrets manager, setting up the RDS database and creating the RDS secret using the secrets manager. It also edits the required configuration files for Kubeflow pipeline to be properly configured for the RDS database during Kubeflow installation.  
The script also handles cases where the resources already exist in which case it will simply skips the step.

Note : The script will **not** delete any resource therefore if a resource already exists (eg: secret, database with the same name or S3 bucket etc), **it will skip the creation of those resources and use the existing resources instead**. This was done in order to prevent unwanted results such as accidental deletion. For instance, if a database with the same name already exists, the script will skip the database creation setup. If it's expected in your scenario, then perhaps this is fine for you, if you simply forgot to change the database name used for creation then this gives you the chance to retry the script with the proper value. See `python auto-rds-s3-setup.py --help` for the list of parameters as well as their default values.

1. Install the script dependencies `pip install -r requirements.txt`
2. Run the script  
   Replace `YOUR_CLUSTER_REGION`, `YOUR_CLUSTER_NAME` and `YOUR_S3_BUCKET` with your values.

```
python auto-rds-s3-setup.py --region YOUR_CLUSTER_REGION --cluster YOUR_CLUSTER_NAME --bucket YOUR_S3_BUCKET
```

### Advanced customization

The script applies some sensible default values for the db user password, max storage, storage type, instance type etc but if you know what you are doing, you can always tweak those preferences by passing different values.  
You can learn more about the different parameters by running `python auto-rds-s3-setup.py --help`.

### 2.2 **Option 2: Manual Setup**
If you prefer to manually setup each components then you can follow this manual guide.  
1. [S3] Create an S3 Bucket

    Refer to the [S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.html) for steps on creating an `S3 bucket`.
  To complete the following steps you will need to keep track of the `S3 bucket name`.

2. [RDS] Create an RDS Instance

    Refer to the [RDS documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.MySQL.html) for steps on creating an `RDS MySQL instance`.
    To complete the following steps you will need to keep track of the following:
    - `RDS database name` (not to be confused with the `DB identifier`)
    - `RDS database admin username`
    - `RDS database admin password`
    - `RDS database endpoint URL`
    - `RDS database port`

3. Create Secrets in AWS Secrets Manager

   1. [RDS] Create the RDS secret and configure the secret provider:
      1. Configure a secret, for example named `rds-secret`, with the RDS DB name, RDS endpoint URL, RDS DB port, and RDS DB credentials that were configured when following the steps in Create RDS Instance.
         - For example, if your database name is `kubeflow`, your endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, your DB port is `3306`, your DB username is `admin`, and your DB password is `Kubefl0w` your secret should look like:
         - ```
           aws secretsmanager create-secret --name rds-secret --secret-string '{"username":"admin","password":"Kubefl0w","database":"kubeflow","host":"rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com","port":"3306"}' --region $CLUSTER_REGION
           ```
      1. Rename the `parameters.objects.objectName` field in [the rds secret provider configuration](../../../awsconfigs/common/aws-secrets-manager/rds/secret-provider.yaml) to the name of the secret. 
         - For example, if your secret name is `rds-secret-new`, the configuration would look like:
         - ```
           apiVersion: secrets-store.csi.x-k8s.io/v1alpha1
           kind: SecretProviderClass
           metadata:
              name: rds-secret

              ...
              
              parameters:
                 objects: | 
                 - objectName: "rds-secret-new" # This line was changed
                   objectType: "secretsmanager"
                   jmesPath:
                      - path: "username"
                         objectAlias: "user"
                      - path: "password"
                         objectAlias: "pass"
                      - path: "host"
                         objectAlias: "host"
                      - path: "database"
                         objectAlias: "database"
                      - path: "port"
                         objectAlias: "port"
           ```
         - One line command:
           ```
           yq e -i '.spec.parameters.objects |= sub("rds-secret","YOUR_SECRET_NAME")' awsconfigs/common/aws-secrets-manager/rds/secret-provider.yaml
           ```
         
   1. [S3] Create the S3 secret and configure the secret provider:
      1. Configure a secret, for example named `s3-secret`, with your AWS credentials. These need to be long term credentials from an IAM user and not temporary.
         - Find more details about configuring/getting your AWS credentials here:
           https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html
         - ```
           aws secretsmanager create-secret --name s3-secret --secret-string '{"accesskey":"AXXXXXXXXXXXXXXXXXX6","secretkey":"eXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXq"}' --region $CLUSTER_REGION
           ```
      1. Rename the `parameters.objects.objectName` field in [the s3 secret provider configuration](../../../awsconfigs/common/aws-secrets-manager/s3/secret-provider.yaml) to the name of the secret. 
         - For example, if your secret name is `s3-secret-new`, the configuration would look like:
         - ```
           apiVersion: secrets-store.csi.x-k8s.io/v1alpha1
           kind: SecretProviderClass
           metadata:
             name: s3-secret

             ...
             
             parameters:
               objects: | 
                 - objectName: "s3-secret-new" # This line was changed
                   objectType: "secretsmanager"
                   jmesPath:
                       - path: "accesskey"
                         objectAlias: "access"
                       - path: "secretkey"
                         objectAlias: "secret"           
           ```
         - One line command:
           ```
           yq e -i '.spec.parameters.objects |= sub("s3-secret","YOUR_SECRET_NAME")' awsconfigs/common/aws-secrets-manager/s3/secret-provider.yaml
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

5. Update the KFP configurations
    1. [RDS] Configure the `awsconfigs/apps/pipeline/rds/params.env` file with the RDS endpoint url and the metadata db name.

       For example, if your RDS endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com` and your metadata db name is `kubeflow` your `params.env` file should look like:
       ```
        dbHost=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com
        mlmdDb=kubeflow
        ```

    2. [S3] Configure the `awsconfigs/apps/pipeline/s3/params.env` file with with the `S3 bucket name`, and `S3 bucket region`..

         For example, if your S3 bucket name is `kf-aws-demo-bucket` and s3 bucket region is `us-west-2` your `params.env` file should look like:
         ```
          bucketName=kf-aws-demo-bucket
          minioServiceHost=s3.amazonaws.com
          minioServiceRegion=us-west-2
          ```

## 3.0 Build Manifests and Install Kubeflow

Once you have the resources ready, you can continue on to deploying the Kubeflow manifests using the single line command below -

Choose your deployment option below from:

- Deploying the configuration for both RDS and S3
- Deploying the configuration for RDS only
- Deploying the configuration for S3 only

#### [RDS and S3] Deploy both RDS and S3

```sh
while ! kustomize build docs/deployment/rds-s3 | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

#### [RDS] Deploy RDS only

```sh
while ! kustomize build docs/deployment/rds-s3/rds-only | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

#### [S3] Deploy S3 only

```sh
while ! kustomize build docs/deployment/rds-s3/s3-only | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

Once, everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster](../vanilla/README.md#connect-to-your-kubeflow-cluster).

Congratulations! You can now start experimenting and running your end-to-end ML workflows with Kubeflow.


## 4.0 Verify the installation

### 4.1 Verify RDS

1. Connect to the RDS instance from a pod within the cluster

```
kubectl run -it --rm --image=mysql:5.7 --restart=Never mysql-client -- mysql -h <YOUR RDS ENDPOINT> -u <YOUR LOGIN> -p<YOUR PASSWORD>
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

4. Access the Kubeflow Central Dashboard [by logging in to your cluster](../vanilla/README.md#connect-to-your-kubeflow-cluster) and navigate to Katib (under Experiments (AutoML)).

5. Create an experiment using the following [yaml file](../../../tests/e2e/resources/custom-resource-templates/katib-experiment-random.yaml).

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

1. Access the Kubeflow Central Dashboard [by logging in to your cluster](../vanilla/README.md#connect-to-your-kubeflow-cluster) and navigate to Kubeflow Pipelines (under Pipelines).

2. Create an experiment named `test` and create a run using the sample pipeline `[Demo] XGBoost - Iterative model training`.

3. Once the run is completed go to the S3 AWS console and open the bucket you specified for the Kubeflow installation.

4. Verify the bucket is not empty and was populated by outputs of the experiment.

## 5.0 Uninstall Kubeflow

Run the following command to uninstall:

```sh
kustomize build docs/deployment/rds-s3 | kubectl delete -f -
```

Additionally, the following cleanup steps may be required:

```sh
kubectl delete mutatingwebhookconfigurations.admissionregistration.k8s.io webhook.eventing.knative.dev webhook.istio.networking.internal.knative.dev webhook.serving.knative.dev

kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io config.webhook.eventing.knative.dev config.webhook.istio.networking.internal.knative.dev config.webhook.serving.knative.dev

kubectl delete endpoints -n default mxnet-operator pytorch-operator tf-operator
```
