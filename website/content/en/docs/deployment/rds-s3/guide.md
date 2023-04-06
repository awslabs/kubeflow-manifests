+++
title = "Manifest Deployment Guide"
description = "Deploying Kubeflow with RDS and S3 using Kustomize or Helm"
weight = 20
+++

> Note: Helm installation option is still in preview.

This guide can be used to deploy Kubeflow Pipelines (KFP) and Katib with RDS and S3.

### RDS

[Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html) is a managed relational database service that facilitates several database management tasks such as database scaling, database backups, database software patching, OS patching, and more.

In the [default Kubeflow installation]({{< ref "/docs/deployment/vanilla/guide.md" >}}), the [KFP](https://github.com/kubeflow/manifests/blob/v1.5-branch/apps/pipeline/upstream/third-party/mysql/base/mysql-deployment.yaml) and [Katib](https://github.com/kubeflow/manifests/blob/v1.5-branch/apps/katib/upstream/components/mysql/mysql.yaml) components both use their own MySQL pod to persist KFP data (such as experiments, pipelines, jobs, etc.) and Katib experiment observation logs, respectively. 

Compared to the MySQL setup in the default installation, using RDS provides the following advantages:
- Availability: RDS provides high availability and failover support for DB instances using Multi Availability Zone (Mulit-AZ) deployments with a single standby DB instance, increasing the availability of KFP and Katib services during unexpected network events.
- Scalability: RDS can be configured to handle availability and scaling needs. The default Kubeflow installation uses an EBS-hosted Persistent Volume Claim that is AZ-bound and does not support automatic online resizing.
- Persistent data: KFP and Katib data can persist beyond single Kubeflow installations. Using RDS decouples the KFP and Katib datastores from the Kubeflow deployment, allowing multiple Kubeflow installations to reuse the same RDS instance provided that the KFP component versions store data in a format that is compatible.
- Customization and management: RDS provides management features to facilitate changing database instance types, updating SQL versions, and more.

### S3
[Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) is an object storage service that is highly scalable, available, secure, and performant. 

In the [default Kubeflow installation]({{< ref "/docs/deployment/vanilla/guide.md" >}}), the [KFP](https://github.com/kubeflow/manifests/blob/v1.4-branch/apps/pipeline/upstream/third-party/minio/base/minio-deployment.yaml) component uses the MinIO object storage service that can be configured to store objects in S3. However, by default the installation hosts the object store service locally in the cluster. KFP stores data such as pipeline architectures and pipeline run artifacts in MinIO.

Configuring MinIO to read and write to S3 provides the following advantages:
- Scalability and availability: S3 offers industry-leading scalability and availability and is more durable than the default MinIO object storage solution provided by Kubeflow.
- Persistent artifacts: KFP artifacts can persist beyond single Kubeflow installations. Using S3 decouples the KFP artifact store from the Kubeflow deployment, allowing multiple Kubeflow installations to access the same artifacts provided that the KFP component versions store data in a format that is compatible.
- Customization and management: S3 provides management features to help optimize, organize, and configure access to your data to meet your specific business, organizational, and compliance requirements.

To get started with configuring and installing your Kubeflow installation with RDS and S3 follow the [install](#install) steps below to configure and deploy the Kustomize manifest.

## Install

The following steps show how to configure and deploy Kubeflow with supported AWS services.

### Using only RDS or only S3

Steps relevant only to the RDS installation are prefixed with `[RDS]`.

Steps relevant only to the S3 installation are prefixed with `[S3]`.

Steps without any prefixing are necessary for all installations.

To install for only RDS or only S3, complete the steps relevant to your installation choice.

To install for both RDS and S3, complete all the steps below.

## 1.0 Prerequisites
Follow the steps in [Prerequisites]({{< ref "/docs/deployment/prerequisites.md" >}}) to make sure that you have everything you need to get started. 

Make sure you are starting from the repository root directory. 
Export the below variable:
```bash
export REPO_ROOT=$(pwd)
```

## 2.0 Set up RDS, S3, and configure Secrets

There are two ways to create RDS and S3 resources before you deploy the Kubeflow manifests. Either use the [automated setup](#21-option-1-automated-setup) Python script that is mentioned in the following step, or follow the [manual setup instructions](#22-option-2-manual-setup).

### 2.1 **Option 1: Automated Setup**

This setup performs all the manual steps in an automated fashion.  

The script takes care of creating the S3 bucket, creating the S3 Secrets using the Secrets manager, setting up the RDS database, and creating the RDS Secret using the Secrets manager. The script also edits the required configuration files for Kubeflow Pipelines to be properly configured for the RDS database during Kubeflow installation. The script also handles cases where the resources already exist. In this case, the script will simply skip the step.

> Note: The script will **not** delete any resource. Therefore, if a resource already exists (eg: Secret, database with the same name, or S3 bucket), **it will skip the creation of those resources and use the existing resources instead**. This is by design in order to prevent unwanted results, such as accidental deletion. For example, if a database with the same name already exists, the script will skip the database creation setup. If you forgot to change the database name used for creation, then this gives you the chance to retry the script with the proper value. See `python auto-rds-s3-setup.py --help` for the list of parameters, as well as their default values.

1. Navigate to the `tests/e2e` directory.
   ```bash
   cd tests/e2e
   ```
1. [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_cliwpsapi) with permissions to get bucket locations and allow read and write access to objects in an S3 bucket where you want to store the Kubeflow artifacts. Take note of the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` of the IAM user that you created to use in the following step, which will be referenced as `MINIO_AWS_ACCESS_KEY_ID` and `MINIO_AWS_SECRET_ACCESS_KEY` respectively.
1. Export values for `CLUSTER_REGION`, `CLUSTER_NAME`, `S3_BUCKET`, `MINIO_AWS_ACCESS_KEY_ID`, and `MINIO_AWS_SECRET_ACCESS_KEY`.
   ```bash
   export CLUSTER_REGION=<>
   export CLUSTER_NAME=<>
   export S3_BUCKET=<>
   export DB_INSTANCE_NAME=<>
   export DB_SUBNET_GROUP_NAME=<>
   export MINIO_AWS_ACCESS_KEY_ID=<>
   export MINIO_AWS_SECRET_ACCESS_KEY=<>
   export RDS_SECRET_NAME=<>
   export S3_SECRET_NAME=<>
   ```
1. Run the `auto-rds-s3-setup.py` script
   ```
   PYTHONPATH=.. python utils/rds-s3/auto-rds-s3-setup.py --region $CLUSTER_REGION --cluster $CLUSTER_NAME --bucket $S3_BUCKET --s3_aws_access_key_id $MINIO_AWS_ACCESS_KEY_ID --s3_aws_secret_access_key $MINIO_AWS_SECRET_ACCESS_KEY --db_instance_name $DB_INSTANCE_NAME --s3_secret_name $S3_SECRET_NAME --rds_secret_name $RDS_SECRET_NAME --db_subnet_group_name $DB_SUBNET_GROUP_NAME
   ```  

### Advanced customization

The `auto-rds-s3-setup.py` script applies default values for the user password, max storage, storage type, instance type, and more. You can customize those preferences by specifying different values.  

Learn more about the different parameters with the following command:
```bash
PYTHONPATH=.. python utils/rds-s3/auto-rds-s3-setup.py --help
```

### 2.2 **Option 2: Manual Setup**
Follow this step if you prefer to manually set up each component. 
1. [S3] Create an S3 Bucket

    Refer to the [S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/GetStartedWithS3.html) for steps on creating an `S3 bucket`.
  Take note of your `S3 bucket name` to use in the following steps.

2. [RDS] Create an RDS Instance

    Refer to the [RDS documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_GettingStarted.CreatingConnecting.MySQL.html) for steps on creating an `RDS MySQL instance`.

    When creating the RDS instance for security and connectivity reasons, we recommend that:
    - The RDS instance is in the same VPC as the cluster
    - The RDS instance subnets must belong to at least two private subnets within the VPC
    - The RDS instance security group is the same security group used by the EKS node instances

    To complete the following steps you will need to keep track of the following:
    - `RDS database name` (not to be confused with the `DB identifier`)
    - `RDS database admin username`
    - `RDS database admin password`
    - `RDS database endpoint URL`
    - `RDS database port`

3. [S3] Create IAM User With Permissions To S3 Bucket

   [Create an IAM user](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_cliwpsapi) with permissions to get bucket locations and allow read and write access to objects in an S3 bucket where you want to store the Kubeflow artifacts. Take note of the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` of the IAM user that you created to use in the following step, which will be referenced as `MINIO_AWS_ACCESS_KEY_ID` and `MINIO_AWS_SECRET_ACCESS_KEY` respectively.

1. Export values:
    ```bash
    export RDS_SECRET="<your rds secret name>"
    export S3_SECRET="<your s3 secret name>"
    export DB_HOST="<your rds db host>"
    export MLMD_DB=metadata_db
    export S3_BUCKET="<your s3 bucket name>"
    export MINIO_SERVICE_HOST=s3.amazonaws.com
    export MINIO_AWS_ACCESS_KEY_ID="<your s3 user access key>"
    export MINIO_AWS_SECRET_ACCESS_KEY="<your s3 user secret key>"
    ```

3. Create Secrets in AWS Secrets Manager

   1. [RDS] Create the RDS Secret and configure the Secret provider:
      1. Configure a Secret (e.g `rds-secret`), with the RDS DB name, RDS endpoint URL, RDS DB port, and RDS DB credentials that were configured when creating your RDS instance.
         - For example, if your database name is `kubeflow`, your endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, your DB port is `3306`, your DB username is `admin`, and your DB password is `Kubefl0w` your secret should look similar to the following:
         - ```bash
           aws secretsmanager create-secret --name $RDS_SECRET --secret-string '{"username":"admin","password":"Kubefl0w","database":"kubeflow","host":"rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com","port":"3306"}' --region $CLUSTER_REGION
           ```
      1. Rename the `parameters.objects.objectName` field in [the RDS Secret provider configuration](https://github.com/awslabs/kubeflow-manifests/blob/main/awsconfigs/common/aws-secrets-manager/rds/secret-provider.yaml) to the name of the Secret. 
         - Rename the field with the following command:
            Select the package manager of your choice.
            {{< tabpane persistLang=false >}}
            {{< tab header="Kustomize" lang="toml" >}}
yq e -i '.spec.parameters.objects |= sub("rds-secret",env(RDS_SECRET))' awsconfigs/common/aws-secrets-manager/rds/secret-provider.yaml
            {{< /tab >}}
            {{< tab header="Helm" lang="yaml" >}}
yq e '.rds.secretName = env(RDS_SECRET)' -i charts/common/aws-secrets-manager/rds-only/values.yaml
yq e '.rds.secretName = env(RDS_SECRET)' -i charts/common/aws-secrets-manager/rds-s3/values.yaml
            {{< /tab >}}
            {{< /tabpane >}} 

         
   1. [S3] Create the S3 Secret and configure the Secret provider:
      1. Configure a Secret (e.g. `s3-secret`) with your AWS credentials. These need to be long-term credentials from an IAM user and not temporary.
         - For more details about configuring or finding your AWS credentials, see [AWS security credentials](https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html)
         - ```bash
           aws secretsmanager create-secret --name $S3_SECRET --secret-string '{"accesskey":"'$MINIO_AWS_ACCESS_KEY_ID'","secretkey":"'$MINIO_AWS_SECRET_ACCESS_KEY'"}' --region $CLUSTER_REGION
           ```
      1. Rename the `parameters.objects.objectName` field in [the S3 Secret provider configuration](https://github.com/awslabs/kubeflow-manifests/blob/main/awsconfigs/common/aws-secrets-manager/s3/secret-provider.yaml) to the name of the Secret. 
         - Rename the field with the following command:
            Select the package manager of your choice.
            {{< tabpane persistLang=false >}}
            {{< tab header="Kustomize" lang="toml" >}}
yq e -i '.spec.parameters.objects |= sub("s3-secret",env(S3_SECRET))' awsconfigs/common/aws-secrets-manager/s3/secret-provider.yaml
            {{< /tab >}}
            {{< tab header="Helm" lang="yaml" >}}
yq e '.s3.secretName = env(S3_SECRET)' -i charts/common/aws-secrets-manager/s3-only/values.yaml
yq e '.s3.secretName = env(S3_SECRET)' -i charts/common/aws-secrets-manager/rds-s3/values.yaml
            {{< /tab >}}
            {{< /tabpane >}}


4. Install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver

   1. Run the following commands to enable OIDC and create an `iamserviceaccount` with permissions to retrieve the Secrets created with AWS Secrets Manager.

   ```bash
   eksctl utils associate-iam-oidc-provider --region=$CLUSTER_REGION --cluster=$CLUSTER_NAME --approve

   eksctl create iamserviceaccount  --name kubeflow-secrets-manager-sa  --namespace kubeflow  --cluster $CLUSTER_NAME --attach-policy-arn  arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite --override-existing-serviceaccounts   --approve --region $CLUSTER_REGION
   ```

   2. Run the following commands to install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver:

   ```bash
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/rbac-secretproviderclass.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/csidriver.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store-csi-driver.yaml
    kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/rbac-secretprovidersyncing.yaml
    kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
   ```

5. Update the KFP configurations.
    1. [RDS] Configure the *RDS endpoint URL* and *the metadata DB name*:
         - Rename the field with the following command
            Select the package manager of your choice.
            {{< tabpane persistLang=false >}}
            {{< tab header="Kustomize" lang="toml" >}}
printf '
dbHost='$DB_HOST'
mlmdDb='$MLMD_DB'
' > awsconfigs/apps/pipeline/rds/params.env
            {{< /tab >}}
            {{< tab header="Helm" lang="yaml" >}}
yq e '.rds.dbHost = env(DB_HOST)' -i charts/apps/kubeflow-pipelines/rds-s3/values.yaml
yq e '.rds.dbHost = env(DB_HOST)' -i charts/apps/kubeflow-pipelines/rds-only/values.yaml
yq e '.rds.mlmdDb = env(MLMD_DB)' -i charts/apps/kubeflow-pipelines/rds-s3/values.yaml
yq e '.rds.mlmdDb = env(MLMD_DB)' -i charts/apps/kubeflow-pipelines/rds-only/values.yaml
            {{< /tab >}}
            {{< /tabpane >}}
       

    2. [S3] Configure the *S3 bucket name* and *S3 bucket region*: 

         Select the package manager of your choice.
            {{< tabpane persistLang=false >}}
            {{< tab header="Kustomize" lang="toml" >}}
printf '
bucketName='$S3_BUCKET'
minioServiceHost='$MINIO_SERVICE_HOST'
minioServiceRegion='$CLUSTER_REGION'
' > awsconfigs/apps/pipeline/s3/params.env
            {{< /tab >}}
            {{< tab header="Helm" lang="yaml" >}}
yq e '.s3.bucketName = env(S3_BUCKET)' -i charts/apps/kubeflow-pipelines/rds-s3/values.yaml
yq e '.s3.minioServiceRegion = env(CLUSTER_REGION)' -i charts/apps/kubeflow-pipelines/rds-s3/values.yaml
yq e '.s3.minioServiceHost = env(MINIO_SERVICE_HOST)' -i charts/apps/kubeflow-pipelines/rds-s3/values.yaml
yq e '.s3.bucketName = env(S3_BUCKET)' -i charts/apps/kubeflow-pipelines/s3-only/values.yaml
yq e '.s3.minioServiceHost = env(MINIO_SERVICE_HOST)' -i charts/apps/kubeflow-pipelines/s3-only/values.yaml
yq e '.s3.minioServiceRegion = env(CLUSTER_REGION)' -i charts/apps/kubeflow-pipelines/s3-only/values.yaml
            {{< /tab >}}
            {{< /tabpane >}}

### (Optional) Configure Culling for Notebooks
Enable culling for notebooks by following the [instructions]({{< ref "/docs/deployment/configure-notebook-culling.md#" >}}) in configure culling for notebooks guide. 


## 3.0 Build Manifests and install Kubeflow

Once you have the resources ready, you can deploy the Kubeflow manifests for one of the following deployment options:
- both RDS and S3
- RDS only
- S3 only

Navigate to the root of repository

```bash
cd $REPO_ROOT
```

#### [RDS and S3] Deploy both RDS and S3

Use the following command to deploy the Kubeflow manifests for both RDS and S3:
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=rds-s3
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=rds-s3
{{< /tab >}}
{{< /tabpane >}}

#### [RDS] Deploy RDS only

Use the following command to deploy the Kubeflow manifests for RDS only:
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=rds-only
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=rds-only
{{< /tab >}}
{{< /tabpane >}}


#### [S3] Deploy S3 only

Use the following command to deploy the Kubeflow manifests for S3 only:
{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make deploy-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=s3-only
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make deploy-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=s3-only
{{< /tab >}}
{{< /tabpane >}}

Once everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster]({{< ref "/docs/deployment/vanilla/guide.md#connect-to-your-kubeflow-cluster" >}}).

You can now start experimenting and running your end-to-end ML workflows with Kubeflow!

## 4.0 Verify the installation

### 4.1 Verify RDS

1. Connect to your RDS instance from a pod within the cluster with the following command:
```bash
kubectl run -it --rm --image=mysql:5.7 --restart=Never mysql-client -- mysql -h <YOUR RDS ENDPOINT> -u <YOUR LOGIN> -p<YOUR PASSWORD>
```

You can find your credentials by visiting [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/) or by using the [AWS CLI](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/secretsmanager/get-secret-value.html).

For example, use the following command to retrieve the value of a Secret named `rds-secret`:
```bash
aws secretsmanager get-secret-value \
    --region $CLUSTER_REGION \
    --secret-id $RDS_SECRET_NAME \
    --query 'SecretString' \
    --output text
```

2. Once you are connected to your RDS instance, verify that the databases `kubeflow` and `mlpipeline` exist.
```bash
mysql> show databases;

+--------------------+
| Database           |
+--------------------+
| cachedb            |
| information_schema |
| kubeflow           |
| metadb             |
| mlpipeline         |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
```

3. Verify that the database `mlpipeline` has the following tables:
```bash
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
| tasks                |
+----------------------+
```

4. Access the Kubeflow Central Dashboard [by logging in to your cluster]({{< ref "/docs/deployment/vanilla/guide.md#connect-to-your-kubeflow-cluster" >}}) and navigate to Katib (under Experiments (AutoML)).

5. Create an experiment using the following [yaml file](https://github.com/awslabs/kubeflow-manifests/blob/main/tests/e2e/resources/custom-resource-templates/katib-experiment-random.yaml).

6. Once the experiment is complete, verify that the following table exists:
```bash
mysql> use kubeflow; show tables;

+----------------------+
| Tables_in_kubeflow   |
+----------------------+
| observation_logs     |
+----------------------+
```

7. Describe the `observation_logs` to verify that they are being populated.
```bash
mysql> select * from observation_logs;
```

### 4.2 Verify S3

1. Access the Kubeflow Central Dashboard [by logging in to your cluster]({{< ref "/docs/deployment/vanilla/guide.md#connect-to-your-kubeflow-cluster" >}}) and navigate to Kubeflow Pipelines (under Pipelines).

2. Create an experiment named `test` and create a run using the sample pipeline `[Demo] XGBoost - Iterative model training`.

3. Once the run is completed, go to the S3 AWS console and open the bucket that you specified for your Kubeflow installation.

4. Verify that the bucket is not empty and was populated by the outputs of the experiment.

## 5.0 Uninstall Kubeflow

Run the following command to uninstall your Kubeflow deployment:

> Note: Make sure you have the correct INSTALLATION_OPTION and DEPLOYMENT_OPTION environment variables set for your chosen installation


{{< tabpane persistLang=false >}}
{{< tab header="Kustomize" lang="toml" >}}
make delete-kubeflow INSTALLATION_OPTION=kustomize DEPLOYMENT_OPTION=rds-s3
{{< /tab >}}
{{< tab header="Helm" lang="yaml" >}}
make delete-kubeflow INSTALLATION_OPTION=helm DEPLOYMENT_OPTION=rds-s3
{{< /tab >}}
{{< /tabpane >}}

To uninstall AWS resources created by the automated setup, run the cleanup script:
1. Navigate to the `tests/e2e` directory.
```bash
cd tests/e2e
```
2. Install the script dependencies. 
```bash
pip install -r requirements.txt
```
3. Make sure that you have the configuration file created by the script in `tests/e2e/utils/rds-s3/metadata.yaml`.
```bash
PYTHONPATH=.. python utils/rds-s3/auto-rds-s3-cleanup.py
```  
