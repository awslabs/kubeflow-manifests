# Kustomize Manifests for RDS and S3

## Overview
This Kustomize Manifest can be used to deploy Kubeflow Pipelines and Katib with RDS and S3.

Follow the [install](#install) steps below to configure and deploy the Kustomize manifest.

## Provisioning AWS Resources 

### Create S3 Bucket

Run this command to create S3 bucket by changing `<YOUR_S3_BUCKET_NAME>` and `<YOUR_CLUSTER_REGION` to the preferred settings.

```
export S3_BUCKET=<YOUR_S3_BUCKET_NAME>
export CLUSTER_REGION=<YOUR_CLUSTER_REGION>
aws s3 mb s3://$S3_BUCKET --region $CLUSTER_REGION
```

### Create RDS Instance

Follow this [doc](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/rds/#deploy-amazon-rds-mysql) to set up an AWS RDS instance.

## Install

### Install with a single command

Similar to [the single command base installation](../../../README.md#base-install-with-a-single-command) the AWS install configures the Kubeflow official components to integrate with supported AWS services. 

The following sections show how to configure the respective Kubeflow components:
- [Kubeflow Pipelines](#kubeflow-pipelines-with-rds-and-s3)
- [Katib](#katib-with-rds)


Once configured, install using the following command:

```sh
while ! kustomize build . | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

Once, everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster](../../../README.md#connect-to-your-kubeflow-cluster).

Congratulations! You can now start experimenting and running your end-to-end ML workflows with Kubeflow.

### Install individual components

#### Kubeflow Pipelines with RDS and S3

Make sure you have followed the steps at [Create RDS Instance](#create-rds-instance) to prepare your RDS MySQL database for integration with Kubeflow Pipelines. 

Make sure you have also followed the steps at [Create S3 Bucket](#create-s3-bucket) to prepare your S3 for integration with Kubeflow Pipelines. 

1. Go to the pipelines manifest directory `<KUBEFLOW_MANIFESTS_REPO_PATH>/apps/pipeline/upstream/env/aws`
```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>/apps/pipeline/upstream/env/aws/
```

2. Configure `params.env` with the RDS endpoint URL, S3 bucket name, and S3 bucket region that were configured when following the steps in [Create RDS Instance](#create-rds-instance) and [Create S3 Bucket](#create-s3-bucket). 

- For example if your RDS endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, S3 bucket name is `kf-aws-demo-bucket`, and s3 bucket region is `us-west-2` your `params.env` file should look like:

```
dbHost=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com

bucketName=kf-aws-demo-bucket
minioServiceHost=s3.amazonaws.com
minioServiceRegion=us-west-2
```

3. Configure `secret.env` with your RDS database username and password that were configured when following the steps in [Create RDS Instance](#create-rds-instance). 

- For example if your username is `admin` and your password is `Kubefl0w` then your `secret.env` file should look like:

```
username=admin
password=Kubefl0w
```

4. Configure `minio-artifact-secret-patch.env` with your AWS credentials.

Find more details about configuring/getting your AWS credentials here:
https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html

```
accesskey=AXXXXXXXXXXXXXXXXXX6
secretkey=eXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXq
```

5. [Single component installation] Install

```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>
kustomize build apps/pipeline/upstream/env/aws/ | kubectl apply -f -

# If upper one action got failed, e.x. you used wrong value, try delete, fix and apply again
kustomize build apps/pipeline/upstream/env/aws/ | kubectl delete -f -
```

#### Katib with RDS

Make sure you have followed the steps at [Create RDS Instance](#create-rds-instance) to prepare your RDS MySQL database for integration with Kubeflow Pipelines. 

1. Go to the katib manifests directory `apps/katib/upstream/installs/katib-external-db-with-kubeflow`
```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>/apps/katib/upstream/installs/katib-external-db
```

2. Configure `secrets.env` with the RDS DB name, RDS endpoint URL, RDS DB port, and RDS DB credentials that were configured when following the steps in [Create RDS Instance](#create-rds-instance).

- For example if your database name is `KubeflowRDS`, your endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, your DB port is `3306`, your DB username is `admin`, and your DB password is `Kubefl0w` your `secrets.env` file should look like:
```
KATIB_MYSQL_DB_DATABASE=KubeflowRDS1
KATIB_MYSQL_DB_HOST=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com
KATIB_MYSQL_DB_PORT=3306
DB_USER=admin
DB_PASSWORD=Kubefl0w
```

3. [Single component installation] Install
```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>
kustomize build /apps/katib/upstream/installs/katib-external-db-with-kubeflow | kubectl apply -f - 
```

## Uninstall

If Kubeflow was installed by following a single command installation Kubeflow can be uninstalled by running the respective commands
```sh
kustomize build examples/aws | kubectl delete -f -
```

Individual components can usually be uninstalled by following:

```sh
kustomize build <PATH_TO_COMPONENT_MANIFEST> | kubectl delete -f -
```

Warning: This command may delete the `kubeflow` namespace depending on the Kustomization manifest of the component.

Additionally, the following cleanup steps may be required:

```sh
kubectl delete mutatingwebhookconfigurations.admissionregistration.k8s.io webhook.eventing.knative.dev webhook.istio.networking.internal.knative.dev webhook.serving.knative.dev

kubectl delete validatingwebhookconfigurations.admissionregistration.k8s.io config.webhook.eventing.knative.dev config.webhook.istio.networking.internal.knative.dev config.webhook.serving.knative.dev

kubectl delete endpoints -n default mxnet-operator pytorch-operator tf-operator
```