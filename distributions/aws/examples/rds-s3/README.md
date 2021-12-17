# Kustomize Manifests for RDS and S3

## Overview
This Kustomize Manifest can be used to deploy Kubeflow Pipelines and Katib with RDS and S3.

Follow the [install](#install) steps below to configure and deploy the Kustomize manifest.

## Install

Similar to [the single command base installation](../../../../README.md#install-with-a-single-command) the AWS install configures the Kubeflow official components to integrate with supported AWS services. 

The following steps show how to configure and deploy:

### 1. Prerequisites

1. Install CLI tools
    - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
    - [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
    - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
    - [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://mikefarah.gitbook.io/yq/#wget))
    - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
    - [kustomize](https://kubectl.docs.kubernetes.io/installation/kustomize/) - A command line tool to customize Kubernetes objects through a kustomization file.

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

4. Create S3 Bucket

Run this command to create S3 bucket by changing `<YOUR_S3_BUCKET_NAME>` and `<YOUR_CLUSTER_REGION` to the preferred settings.

```
export S3_BUCKET=<YOUR_S3_BUCKET_NAME>
export CLUSTER_REGION=<YOUR_CLUSTER_REGION>
aws s3 mb s3://$S3_BUCKET --region $CLUSTER_REGION
```

5. Create RDS Instance

Follow this [doc](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/rds/#deploy-amazon-rds-mysql) to set up an AWS RDS instance. Please follow only section called `Deploy Amazon RDS MySQL`. 

6. Install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver

Run the following commands to enable oidc and create an iamserviceaccount with permissions to retrieve secrets from AWS Secrets Manager

```
eksctl utils associate-iam-oidc-provider --region=$CLUSTER_REGION --cluster=$CLUSTER_NAME --approve

kubectl create namespace kubeflow

eksctl create iamserviceaccount  --name kubeflow-secrets-manager-sa  --namespace kubeflow  --cluster $CLUSTER_NAME --attach-policy-arn  arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess --attach-policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite --override-existing-serviceaccounts   --approve --region $CLUSTER_REGION
```

Run these commands to install AWS Secrets & Configuration Provider with Kubernetes Secrets Store CSI driver
```
# You will first need to clone the secrets-store-csi-driver repo.
git clone -b v1.0.0 --single-branch https://github.com/kubernetes-sigs/secrets-store-csi-driver.git && cd secrets-store-csi-driver
kubectl apply -f deploy/rbac-secretproviderclass.yaml
kubectl apply -f deploy/csidriver.yaml
kubectl apply -f deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml
kubectl apply -f deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml
kubectl apply -f deploy/secrets-store-csi-driver.yaml
kubectl apply -f deploy/rbac-secretprovidersyncing.yaml

kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

### 2. Configure Kubeflow Pipelines

1. Configure the following files in `apps/pipeline/upstream/env/aws` directory:

    1. Configure `apps/pipeline/upstream/env/aws/params.env` file with the RDS endpoint URL, S3 bucket name, and S3 bucket region that were configured when following the steps in Create RDS Instance and Create S3 Bucket steps in prerequisites(#1-prerequisites). 
        - For example, if your RDS endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, S3 bucket name is `kf-aws-demo-bucket`, and s3 bucket region is `us-west-2` your `params.env` file should look like:
        - ```
          dbHost=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com

          bucketName=kf-aws-demo-bucket
          minioServiceHost=s3.amazonaws.com
          minioServiceRegion=us-west-2
          ```
    1. Configure an AWS secret with your RDS database username and password that were configured when following the steps in Create RDS Instance.
        - For example, if your username is `admin` and your password is `Kubefl0w` then your secret should look like:
        - **Note:** These are the default values for database credentials in cloudformation template for creating the RDS instance, change these according to the values you used
        - ```
          aws secretsmanager create-secret --name rds-secret --secret-string '{"username":"admin","password":"Kubefl0w"}'  --region $CLUSTER_REGION
          ```
    1. Configure an AWS secret with your AWS credentials. These need to be long term credentials from an IAM user and not temporary. 
        - Find more details about configuring/getting your AWS credentials here:
        https://docs.aws.amazon.com/general/latest/gr/aws-security-credentials.html
        - ```
          aws secretsmanager create-secret --name s3-secret --secret-string '{"accesskey":"AXXXXXXXXXXXXXXXXXX6","secretkey":"eXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXq"}'  --region $CLUSTER_REGION
          ```

### 3. Configure Katib


1. Configure the `apps/katib/upstream/installs/katib-external-db-with-kubeflow/secrets.env` file with the RDS DB name, RDS endpoint URL, RDS DB port, and RDS DB credentials that were configured when following the steps in Create RDS Instance.
    - For example, if your database name is `kubeflow`, your endpoint URL is `rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com`, your DB port is `3306`, your DB username is `admin`, and your DB password is `Kubefl0w` your `secrets.env` file should look like:
    - **Note:** These are the default values for the database name and credentials in cloudformation template for creating the RDS instance, change these according to the values you used
    - ```
      KATIB_MYSQL_DB_DATABASE=kubeflow
      KATIB_MYSQL_DB_HOST=rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com
      KATIB_MYSQL_DB_PORT=3306
      DB_USER=admin
      DB_PASSWORD=Kubefl0w
      ```


### 4. Build Manifests and Install Kubeflow

```sh
while ! kustomize build distributions/aws/examples/rds-s3 | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

Once, everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster](../../../../README.md#connect-to-your-kubeflow-cluster).

Congratulations! You can now start experimenting and running your end-to-end ML workflows with Kubeflow.


## Uninstall Kubeflow

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
