# Kubeflow Manifests

## Kubeflow on AWS Table of Contents
<!-- toc -->

- [Provisioning AWS Resources](#provisioning-aws-resources)
  - [Create EKS Cluster](#create-eks-cluster)
  - [Create S3 Bucket](#create-s3-bucket)
  - [Create RDS Instance](#create-rds-instance)
- [Installation](#installation)
  - [Prerequisites](#prerequisties)
  - [Base installation via `kfctl`](#base-installation-via-kfctl)
  - [Base installation via `kustomize`](#base-installation-via-kustomize)
  - [Kubeflow Pipelines with RDS and S3](#kubeflow-pipelines-with-rds-and-s3)
  - [Katib with RDS](#katib-with-rds)

<!-- tocstop -->
## Provisioning AWS Resources 

### Create EKS Cluster

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
--nodes 2 \
--nodes-min 1 \
--nodes-max 4 \
--managed
```
### Create S3 Bucket

Run this command to create S3 bucket by changing `<YOUR_S3_BUCKET_NAME>` and `<YOUR_CLUSTER_REGION` to the preferred settings.

```
export S3_BUCKET=<YOUR_S3_BUCKET_NAME>
export CLUSTER_REGION=<YOUR_CLUSTER_REGION>
aws s3 mb s3://$S3_BUCKET --region $CLUSTER_REGION
```

### Create RDS Instance

Follow this [doc](https://www.kubeflow.org/docs/distributions/aws/customizing-aws/rds/#deploy-amazon-rds-mysql) to set up an AWS RDS instance.


## Installation

Below is the process to install the basic necessary components to run kubeflow on AWS. The installation can be further integrated with the desired AWS resources by following the following resource specific guides.

### Prerequisties

- Install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/#install-kubectl)
- Install and configure the AWS Command Line Interface (AWS CLI):
    - Install the [AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html).
    - Configure the AWS CLI by running the following command: `aws configure`.
    - Enter your Access Keys ([Access Key ID and Secret Access Key](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys)).
    - Enter your preferred AWS Region and default output options.
- Install [eksctl](https://github.com/weaveworks/eksctl)
- Create an EKS cluster by following the instructions [here](#create-eks-cluster)

### Base installation via `kfctl`

1. Install `kfctl`. Download the kfctl v1.2.0 release from the [Kubeflow releases page](https://github.com/kubeflow/kfctl/releases/tag/v1.2.0).

2. Unpack the tar ball and add the current working directory to your shell’s path to simplify use of `kfctl`.

```
tar -xvf kfctl_v1.2.0_<platform>.tar.gz
export PATH=$PATH:$PWD
```

3. Create a folder for the kubeflow installation manifests with the same name as your cluster.
```
export CLUSTER_NAME=<YOUR_CLUSTER_NAME>
mkdir ${CLUSTER_NAME}
```

4. Copy the `kfctl_aws.v1.3.0.yaml` to the folder you created
```
cp <KUBEFLOW_MANIFESTS_REPO_PATH>/distributions/kfdef/kfctl_aws.v1.3.0.yaml ${CLUSTER_NAME}/
```

5. Go to the installation folder and update `kfctl_aws.v1.3.0.yaml` with the proper `clusterName` and `name` values.
```
cd ${CLUSTER_NAME}
// update kfctl_aws.v1.3.0.yaml with your editor of choice
```

- For example, if your cluster name is `kubeflow-aws-demo` and the cluster region is `us-west-2` append the following fields to your manifest as follows:

```yml
apiVersion: kfdef.apps.kubeflow.org/v1
kind: KfDef
metadata:
  annotations:
    kfctl.kubeflow.io/force-delete: "false"
  clusterName: kubeflow-aws-demo.us-west-2.eksctl.io  # Append cluster name
  creationTimestamp: null
  name: kubeflow-aws-demo # Append name
  namespace: kubeflow
spec:

  ...

```


6. Install kubeflow using `kfctl`
```
kfctl apply -V -f kfctl_aws.v1.3.0.yaml
```

### Base installation via `kustomize`

1. Install kustomize. Installation instructions for your platform can be found here: https://kubectl.docs.kubernetes.io/installation/kustomize/

2. Follow the steps at [Install with a single command](#install-with-a-single-command) to install kubeflow.

### Kubeflow Pipelines with RDS and S3

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

5. [Single-user only] Apply the cluster-scoped-resources manifest.

```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>/apps/pipeline/upstream/env/aws/
kubectl apply -k ../../cluster-scoped-resources
# If upper one action got failed, e.x. you used wrong value, try delete, fix and apply again
# kubectl delete -k ../../cluster-scoped-resources

kubectl wait crd/applications.app.k8s.io --for condition=established --timeout=60s
```

6. [Multi-user only] Make the following change to the kustomization file `<KUBEFLOW_MANIFESTS_REPO_PATH>/apps/pipeline/upstream/env/aws/kustomization.yaml`. 

```yml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: kubeflow
bases:
- ../../env/platform-agnostic-multi-user  # CHANGE THIS LINE from ../../env/platform-agnostic to this
configMapGenerator:
- name: pipeline-install-config
  env: params.env
  behavior: merge
- name: workflow-controller-configmap
  behavior: replace
  files:
  - config
- name: ml-pipeline-ui-configmap
  behavior: replace
  files:
  - viewer-pod-template.json
secretGenerator:
- name: mysql-secret
  env: secret.env
  behavior: merge
- name: mlpipeline-minio-artifact
  env: minio-artifact-secret-patch.env
  behavior: merge
generatorOptions:
  disableNameSuffixHash: true
patchesStrategicMerge:
- aws-configuration-patch.yaml
# Identifier for application manager to apply ownerReference.
# The ownerReference ensures the resources get garbage collected
# when application is deleted.
commonLabels:
  application-crd-id: kubeflow-pipelines
```

7. Install KFP.

```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>/apps/pipeline/upstream/env/aws/
kubectl apply -k ./
# If upper one action got failed, e.x. you used wrong value, try delete, fix and apply again
# kubectl delete -k ./
```
### Katib with RDS

Make sure you have followed the steps at [Create RDS Instance](#create-rds-instance) to prepare your RDS MySQL database for integration with Kubeflow Pipelines. 

1. Go to the katib manifests directory for external databases `apps/katib/upstream/installs/katib-external-db`
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


2. Install
```
cd <KUBEFLOW_MANIFESTS_REPO_PATH>/apps/katib/upstream/installs/katib-external-db
kubectl apply -k ./
```
## Kubeflow Generic Table of Contents

<!-- toc -->

- [Overview](#overview)
- [Kubeflow components versions](#kubeflow-components-versions)
- [Installation](#installation)
  * [Prerequisites](#prerequisites)
  * [Install with a single command](#install-with-a-single-command)
  * [Install individual components](#install-individual-components)
  * [Connect to your Kubeflow Cluster](#connect-to-your-kubeflow-cluster)
  * [Change default user password](#change-default-user-password)
- [Frequently Asked Questions](#frequently-asked-questions)

<!-- tocstop -->
## Overview

This repo is owned by the [Manifests Working Group](https://github.com/kubeflow/community/blob/master/wg-manifests/charter.md).
If you are a contributor authoring or editing the packages please see [Best Practices](./docs/KustomizeBestPractices.md).

The Kubeflow Manifests repository is organized under three (3) main directories, which include manifests for installing:

| Directory | Purpose |
| - | - |
| `apps` | Kubeflow's official components, as maintained by the respective Kubeflow WGs |
| `common` | Common services, as maintained by the Manifests WG |
| `contrib` | 3rd party contributed applications, which are maintained externally and are not part of a Kubeflow WG |

The `distributions` directory contains manifests for specific, opinionated distributions of Kubeflow, and will be phased out during the 1.4 release, [since going forward distributions will maintain their manifests on their respective external repositories](https://github.com/kubeflow/community/blob/master/proposals/kubeflow-distributions.md).

The `docs`, `hack`, and `tests` directories will also be gradually phased out.

Starting Kubeflow 1.3, all components should be deployable using `kustomize` only. Any automation tooling for deployment on top of the manifests should be maintained externally by distribution owners.

## Kubeflow components versions

This repo periodically syncs all official Kubeflow components from their respective upstream repos. The following matrix shows the git version that we include for each component:

| Component | Local Manifests Path | Upstream Revision |
| - | - | - |
| TFJob Operator | apps/tf-training/upstream | [v1.1.0](https://github.com/kubeflow/tf-operator/tree/v1.1.0/manifests) |
| PyTorch Operator | apps/pytorch-job/upstream | [v0.7.0](https://github.com/kubeflow/pytorch-operator/tree/v0.7.0/manifests) |
| MPI Operator | apps/mpi-job/upstream | [b367aa55886d2b042f5089df359d8e067e49e8d1](https://github.com/kubeflow/mpi-operator/tree/b367aa55886d2b042f5089df359d8e067e49e8d1/manifests) |
| MXNet Operator | apps/mxnet-job/upstream | [v1.1.0](https://github.com/kubeflow/mxnet-operator/tree/v1.1.0/manifests) |
| XGBoost Operator | apps/xgboost-job/upstream | [v0.2.0](https://github.com/kubeflow/xgboost-operator/tree/v0.2.0/manifests) |
| Notebook Controller | apps/jupyter/notebook-controller/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/notebook-controller/config) |
| Tensorboard Controller | apps/tensorboard/tensorboard-controller/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/tensorboard-controller/config) |
| Central Dashboard | apps/centraldashboard/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/centraldashboard/manifests) |
| Profiles + KFAM | apps/profiles/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/profile-controller/config) |
| PodDefaults Webhook | apps/admission-webhook/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/admission-webhook/manifests) |
| Jupyter Web App | apps/jupyter/jupyter-web-app/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/crud-web-apps/jupyter/manifests) |
| Tensorboards Web App | apps/tensorboard/tensorboards-web-app/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/crud-web-apps/tensorboards/manifests) |
| Volumes Web App | apps/volumes-web-app/upstream | [v1.3.1-rc.0](https://github.com/kubeflow/kubeflow/tree/v1.3.1-rc.0/components/crud-web-apps/volumes/manifests) |
| Katib | apps/katib/upstream | [v0.11.1](https://github.com/kubeflow/katib/tree/v0.11.1/manifests/v1beta1) |
| KFServing | apps/kfserving/upstream | [e189a510121c09f764f749143b80f6ee6baaf48b (release-0.5)](https://github.com/kubeflow/kfserving/tree/e189a510121c09f764f749143b80f6ee6baaf48b/config) |
| Kubeflow Pipelines | apps/pipeline/upstream | [1.5.1](https://github.com/kubeflow/pipelines/tree/1.5.1/manifests/kustomize) |
| Kubeflow Tekton Pipelines | apps/kfp-tekton/upstream | [v0.8.0](https://github.com/kubeflow/kfp-tekton/tree/v0.8.0/manifests/kustomize) |
## Installation

Starting Kubeflow 1.3, the Manifests WG provides two options for installing Kubeflow official components and common services with kustomize. The aim is to help end users install easily and to help distribution owners build their opinionated distributions from a tested starting point:

1. Single-command installation of all components under `apps` and `common`
2. Multi-command, individual components installation for `apps` and `common`

Option 1 targets ease of deployment for end users. \
Option 2 targets customization and ability to pick and choose individual components.

The `example` directory contains an example kustomization for the single command to be able to run.

:warning: In both options, we use a default email (`user@example.com`) and password (`12341234`). For any production Kubeflow deployment, you should change the default password by following [the relevant section](#change-default-user-password).

### Prerequisites

- `Kubernetes` (tested with version `1.17`) with a default [StorageClass](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- `kustomize` (version `3.2.0`) ([download link](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0))
    - :warning: Kubeflow 1.3.0 is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.
- `kubectl`

---
**NOTE**

`kubectl apply` commands may fail on the first try. This is inherent in how Kubernetes and `kubectl` work (e.g., CR must be created after CRD becomes ready). The solution is to simply re-run the command until it succeeds. For the single-line command, we have included a bash one-liner to retry the command.

---

### Install with a single command

You can install all Kubeflow official components (residing under `apps`) and all common services (residing under `common`) using the following command:

```sh
while ! kustomize build example | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
```

Once, everything is installed successfully, you can access the Kubeflow Central Dashboard [by logging in to your cluster](#connect-to-your-kubeflow-cluster).

Congratulations! You can now start experimenting and running your end-to-end ML workflows with Kubeflow.

### Install individual components

In this section, we will install each Kubeflow official component (under `apps`) and each common service (under `common`) separately, using just `kubectl` and `kustomize`.

If all the following commands are executed, the result is the same as in the above section of the single command installation. The purpose of this section is to:

- Provide a description of each component and insight on how it gets installed.
- Enable the user or distribution owner to pick and choose only the components they need.

#### cert-manager

cert-manager is used by many Kubeflow components to provide certificates for
admission webhooks.

Install cert-manager:

```sh
kustomize build common/cert-manager/cert-manager/base | kubectl apply -f -
kustomize build common/cert-manager/kubeflow-issuer/base | kubectl apply -f -
```

#### Istio

Istio is used by many Kubeflow components to secure their traffic, enforce
network authorization and implement routing policies.

Install Istio:

```sh
kustomize build common/istio-1-9/istio-crds/base | kubectl apply -f -
kustomize build common/istio-1-9/istio-namespace/base | kubectl apply -f -
kustomize build common/istio-1-9/istio-install/base | kubectl apply -f -
```

#### Dex

Dex is an OpenID Connect Identity (OIDC) with multiple authentication backends. In this default installation, it includes a static user with email `user@example.com`. By default, the user's password is `12341234`. For any production Kubeflow deployment, you should change the default password by following [the relevant section](#change-default-user-password).

Install Dex:

```sh
kustomize build common/dex/overlays/istio | kubectl apply -f -
```

#### OIDC AuthService

The OIDC AuthService extends your Istio Ingress-Gateway capabilities, to be able to function as an OIDC client:

```sh
kustomize build common/oidc-authservice/base | kubectl apply -f -
```

#### Knative

Knative is used by the KFServing official Kubeflow component.

Install Knative Serving:

```sh
kustomize build common/knative/knative-serving/base | kubectl apply -f -
kustomize build common/istio-1-9/cluster-local-gateway/base | kubectl apply -f -
```

Optionally, you can install Knative Eventing which can be used for inference request logging:

```sh
kustomize build common/knative/knative-eventing/base | kubectl apply -f -
```

#### Kubeflow Namespace

Create the namespace where the Kubeflow components will live in. This namespace
is named `kubeflow`.

Install kubeflow namespace:

```sh
kustomize build common/kubeflow-namespace/base | kubectl apply -f -
```

#### Kubeflow Roles

Create the Kubeflow ClusterRoles, `kubeflow-view`, `kubeflow-edit` and
`kubeflow-admin`. Kubeflow components aggregate permissions to these
ClusterRoles.

Install kubeflow roles:

```sh
kustomize build common/kubeflow-roles/base | kubectl apply -f -
```

#### Kubeflow Istio Resources

Create the Istio resources needed by Kubeflow. This kustomization currently
creates an Istio Gateway named `kubeflow-gateway`, in namespace `kubeflow`.
If you want to install with your own Istio, then you need this kustomization as
well.

Install istio resources:

```sh
kustomize build common/istio-1-9/kubeflow-istio-resources/base | kubectl apply -f -
```

#### Kubeflow Pipelines

Install the [Multi-User Kubeflow Pipelines](https://www.kubeflow.org/docs/components/pipelines/multi-user/) official Kubeflow component:

```sh
kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user | kubectl apply -f -
```

If your container runtime is not docker, use pns executor instead:

```sh
kustomize build apps/pipeline/upstream/env/platform-agnostic-multi-user-pns | kubectl apply -f -
```

Refer to [argo workflow executor documentation](https://argoproj.github.io/argo-workflows/workflow-executors/#process-namespace-sharing-pns) for their pros and cons.

**Multi-User Kubeflow Pipelines dependencies**

* Istio + Kubeflow Istio Resources
* Kubeflow Roles
* OIDC Auth Service (or cloud provider specific auth service)
* Profiles + KFAM

**Alternative: Kubeflow Pipelines Standalone**

You can install [Kubeflow Pipelines Standalone](https://www.kubeflow.org/docs/components/pipelines/installation/standalone-deployment/) which

* does not support multi user separation
* has no dependencies on the other services mentioned here

You can learn more about their differences in [Installation Options for Kubeflow Pipelines
](https://www.kubeflow.org/docs/components/pipelines/installation/overview/).

Besides installation instructions in Kubeflow Pipelines Standalone documentation, you need to apply two virtual services to expose [Kubeflow Pipelines UI](https://github.com/kubeflow/pipelines/blob/1.5.0-rc.3/manifests/kustomize/base/installs/multi-user/virtual-service.yaml) and [Metadata API](https://github.com/kubeflow/pipelines/blob/1.5.0-rc.3/manifests/kustomize/base/metadata/options/istio/virtual-service.yaml) in kubeflow-gateway.

#### KFServing

Install the KFServing official Kubeflow component:

```sh
kustomize build apps/kfserving/upstream/overlays/kubeflow | kubectl apply -f -
```

#### Katib

Install the Katib official Kubeflow component:

```sh
kustomize build apps/katib/upstream/installs/katib-with-kubeflow | kubectl apply -f -
```

#### Central Dashboard

Install the Central Dashboard official Kubeflow component:

```sh
kustomize build apps/centraldashboard/upstream/overlays/istio | kubectl apply -f -
```

#### Admission Webhook

Install the Admission Webhook for PodDefaults:

```sh
kustomize build apps/admission-webhook/upstream/overlays/cert-manager | kubectl apply -f -
```

#### Notebooks

Install the Notebook Controller official Kubeflow component:

```sh
kustomize build apps/jupyter/notebook-controller/upstream/overlays/kubeflow | kubectl apply -f -
```

Install the Jupyter Web App official Kubeflow component:

```sh
kustomize build apps/jupyter/jupyter-web-app/upstream/overlays/istio | kubectl apply -f -
```

#### Profiles + KFAM

Install the Profile Controller and the Kubeflow Access-Management (KFAM) official Kubeflow
components:

```sh
kustomize build apps/profiles/upstream/overlays/kubeflow | kubectl apply -f -
```

#### Volumes Web App

Install the Volumes Web App official Kubeflow component:

```sh
kustomize build apps/volumes-web-app/upstream/overlays/istio | kubectl apply -f -
```

#### Tensorboard

Install the Tensorboards Web App official Kubeflow component:

```sh
kustomize build apps/tensorboard/tensorboards-web-app/upstream/overlays/istio | kubectl apply -f -
```

Install the Tensorboard Controller official Kubeflow component:

```sh
kustomize build apps/tensorboard/tensorboard-controller/upstream/overlays/kubeflow | kubectl apply -f -
```

#### TFJob Operator

Install the TFJob Operator official Kubeflow component:

```sh
kustomize build apps/tf-training/upstream/overlays/kubeflow | kubectl apply -f -
```

#### PyTorch Operator

Install the PyTorch Operator official Kubeflow component:

```sh
kustomize build apps/pytorch-job/upstream/overlays/kubeflow | kubectl apply -f -
```

#### MPI Operator

Install the MPI Operator official Kubeflow component:

```sh
kustomize build apps/mpi-job/upstream/overlays/kubeflow | kubectl apply -f -
```

#### MXNet Operator

Install the MXNet Operator official Kubeflow component:

```sh
kustomize build apps/mxnet-job/upstream/overlays/kubeflow | kubectl apply -f -
```

#### XGBoost Operator

Install the XGBoost Operator official Kubeflow component:

```sh
kustomize build apps/xgboost-job/upstream/overlays/kubeflow | kubectl apply -f -
```

#### User Namespace

Finally, create a new namespace for the the default user (named `kubeflow-user-example-com`).

```sh
kustomize build common/user-namespace/base | kubectl apply -f -
```

### Connect to your Kubeflow Cluster

After installation, it will take some time for all Pods to become ready. Make sure all Pods are ready before trying to connect, otherwise you might get unexpected errors. To check that all Kubeflow-related Pods are ready, use the following commands:

```sh
kubectl get pods -n cert-manager
kubectl get pods -n istio-system
kubectl get pods -n auth
kubectl get pods -n knative-eventing
kubectl get pods -n knative-serving
kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-user-example-com
```

#### Port-Forward

The default way of accessing Kubeflow is via port-forward. This enables you to get started quickly without imposing any requirements on your environment. Run the following to port-forward Istio's Ingress-Gateway to local port `8080`:

```sh
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

After running the command, you can access the Kubeflow Central Dashboard by doing the following:

1. Open your browser and visit `http://localhost:8080`. You should get the Dex login screen.
2. Login with the default user's credential. The default email address is `user@example.com` and the default password is `12341234`.

#### NodePort / LoadBalancer / Ingress

In order to connect to Kubeflow using NodePort / LoadBalancer / Ingress, you need to setup HTTPS. The reason is that many of our web apps (e.g., Tensorboard Web App, Jupyter Web App, Katib UI) use [Secure Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies#restrict_access_to_cookies), so accessing Kubeflow with HTTP over a non-localhost domain does not work.

Exposing your Kubeflow cluster with proper HTTPS is a process heavily dependent on your environment. For this reason, please take a look at the available Kubeflow distributions, which are targeted to specific environments, and select the one that fits your needs.

---
**NOTE**

If you absolutely need to expose Kubeflow over HTTP, you can disable the `Secure Cookies` feature by setting the `APP_SECURE_COOKIES` environment variable to `false` in every relevant web app. This is not recommended, as it poses security risks.

---

### Change default user password

For security reasons, we don't want to use the default password for the default Kubeflow user when installing in security-sensitive environments. Instead, you should define your own password before deploying. To define a password for the default user:

1. Pick a password for the default user, with email `user@example.com`, and hash it using `bcrypt`:

    ```sh
    python3 -c 'from passlib.hash import bcrypt; import getpass; print(bcrypt.using(rounds=12, ident="2y").hash(getpass.getpass()))'
    ```

2. Edit `dex/base/config-map.yaml` and fill the relevant field with the hash of the password you chose:

    ```yaml
    ...
      staticPasswords:
      - email: user@example.com
        hash: <enter the generated hash here>
    ```

## Frequently Asked Questions

- **Q:** What versions of Istio, Knative, Cert-Manager, Argo, ... are compatible with Kubeflow 1.3? \
  **A:** Please refer to each individual component's documentation for a dependency compatibility range. For Istio, Knative, Dex, Cert-Manager and OIDC-AuthService, the versions in `common` are the ones we have validated.

- **Q:** Can I use the latest Kustomize version (`v4.x`)? \
  **A:** Kubeflow 1.3.0 is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.
