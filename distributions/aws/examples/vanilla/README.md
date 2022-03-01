# Deploying Kubeflow on EKS

This guide describes how to deploy Kubeflow on AWS EKS.

## Prerequisites

This guide assumes that you have:

1. Installed the following tools on the client machine
    - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
    - [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
    - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
    - [yq](https://mikefarah.gitbook.io/yq/) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://github.com/mikefarah/yq/#install))
    - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
    - [kustomize version 3.2.0](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0) - A command line tool to customize Kubernetes objects through a kustomization file.
      - :warning: Kubeflow 1.3.0 is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.

1. Created an EKS cluster
    - If you do not have an existing cluster, run the following command to create an EKS cluster. More details about cluster creation via `eksctl` can be found [here](https://eksctl.io/usage/creating-and-managing-clusters/).
    - Substitute values for the CLUSTER_NAME and CLUSTER_REGION in the script below
        ```
        export CLUSTER_NAME=$CLUSTER_NAME
        export CLUSTER_REGION=$CLUSTER_REGION
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

1. Clone the `awslabs/kubeflow-manifest` repo and checkout release branch.
    1. ```
        git clone https://github.com/awslabs/kubeflow-manifests.git
        cd kubeflow-manifests
        git checkout v1.3-branch
        ```

### Build Manifests and Install Kubeflow

There two options for installing Kubeflow official components and common services with kustomize.

1. Single-command installation of all components under `apps` and `common`
2. Multi-command, individual components installation for `apps` and `common`

Option 1 targets ease of deployment for end users. \
Option 2 targets customization and ability to pick and choose individual components.

:warning: In both options, we use a default email (`user@example.com`) and password (`12341234`). For any production Kubeflow deployment, you should change the default password by following [the relevant section](#change-default-user-password).

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

#### AWS Telemetry

Install the AWS Kubeflow telemetry component. This is an optional component. See the [usage tracking documentation](../README.md#usage-tracking) for more information

```sh
kustomize build distributions/aws/aws-telemetry | kubectl apply -f -
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

#### Exposing Kubeflow over Load Balancer

In order to expose Kubeflow over an external address you can setup AWS ALB, please take a look at the following following comments under the [#67](https://github.com/awslabs/kubeflow-manifests/issues/67) issue: [#67 (comment)](https://github.com/awslabs/kubeflow-manifests/issues/67#issuecomment-1032128251).

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
