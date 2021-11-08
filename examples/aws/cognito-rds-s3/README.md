# Deploying Kubeflow with Amazon Cognito as idP, RDS and S3

This guide describes how to deploy Kubeflow on AWS EKS using Cognito as identity provider, RDS for database and S3 for artifact storage.

## 1. Prerequisites
Follow the pre-requisites section from [this guide](../rds-s3/README.md#1-prerequisites) to:
1. Install the CLI tools
1. Clone the repo
1. Create an EKS cluster and
1. Create S3 Bucket

## Configure Kubeflow Pipelines for RDS and S3

Follow the [Configure Kubeflow Pipelines](../rds-s3/README.md#2-configure-kubeflow-pipelines) section from this guide to:
1. Create an RDS instance
2. Substitute the RDS connection strings and credentials to be used to access the db instance and S3

## Configure Katib for RDS
Follow the [Configure Katib](../rds-s3/README.md#3-configure-katib) section from this guide to:
1. Substitute the RDS connection strings and credentials to be used to access the db instance

## Configure Custom Domain and Cognito

1. Follow the [cognito guide](../cognito/README.md#10-custom-domain) from [section 1.0(Custom Domain)](../cognito/README.md#10-custom-domain) upto step 4 of [section 4.0(Building manifests and deploying Kubeflow)](../cognito/README.md#40-building-manifests-and-deploying-kubeflow) i.e. *Setup resources required for ALB controller* (complete this section) to:
    1. Create a custom domain
    1. Create TLS certificates for the domain
    1. Create a Cognito Userpool
    1. Configuring Ingress and ALB
2. Deploy Kubeflow. Choose one of the two options to deploy kubeflow:
    1. **[Option 1]** Install with a single command
    ```
    while ! kustomize build examples/aws/cognito-rds-s3 | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done
    ```
    1. **[Option 2]** Install individual components
    ```
        # Kubeflow namespace
        kustomize build common/kubeflow-namespace/base | kubectl apply -f -
        
        # Kubeflow Roles
        kustomize build common/kubeflow-roles/base | kubectl apply -f -
        
        # Istio
        kustomize build common/istio-1-9/istio-crds/base | kubectl apply -f -
        kustomize build common/istio-1-9/istio-namespace/base | kubectl apply -f -
        kustomize build common/istio-1-9/istio-install/base | kubectl apply -f -

        # Cert-Manager
        kustomize build common/cert-manager/cert-manager/base | kubectl apply -f -
        kustomize build common/cert-manager/kubeflow-issuer/base | kubectl apply -f -
        
        # KNative
        kustomize build common/knative/knative-serving/base | kubectl apply -f -
        kustomize build common/knative/knative-eventing/base | kubectl apply -f -
        kustomize build common/istio-1-9/cluster-local-gateway/base | kubectl apply -f -
        
        # Kubeflow Istio Resources
        kustomize build common/istio-1-9/kubeflow-istio-resources/base | kubectl apply -f -
        
        
        # KFServing
        kustomize build apps/kfserving/upstream/overlays/kubeflow | kubectl apply -f -
        
        
        # Central Dashboard
        kustomize build apps/centraldashboard/upstream/overlays/istio | kubectl apply -f -
        
        # Notebooks
        kustomize build apps/jupyter/notebook-controller/upstream/overlays/kubeflow | kubectl apply -f -
        kustomize build apps/jupyter/jupyter-web-app/upstream/overlays/istio | kubectl apply -f -
        
        # Admission Webhook
        kustomize build apps/admission-webhook/upstream/overlays/cert-manager | kubectl apply -f -
        
        # Profiles + KFAM
        kustomize build apps/profiles/upstream/overlays/kubeflow | kubectl apply -f -
        
        # Volumes Web App
        kustomize build apps/volumes-web-app/upstream/overlays/istio | kubectl apply -f -
        
        # Tensorboard
        kustomize build apps/tensorboard/tensorboards-web-app/upstream/overlays/istio | kubectl apply -f -
        kustomize build apps/tensorboard/tensorboard-controller/upstream/overlays/kubeflow | kubectl apply -f -
        
        # TFJob Operator
        kustomize build apps/tf-training/upstream/overlays/kubeflow | kubectl apply -f -
        
        # Pytorch Operator
        kustomize build apps/pytorch-job/upstream/overlays/kubeflow | kubectl apply -f -
        
        # MPI Operator
        kustomize build apps/mpi-job/upstream/overlays/kubeflow | kubectl apply -f -
        
        # MXNet Operator
        kustomize build apps/mxnet-job/upstream/overlays/kubeflow | kubectl apply -f -
        
        # XGBoost Operator
        kustomize build apps/xgboost-job/upstream/overlays/kubeflow | kubectl apply -f -

        # Kubeflow Pipelines
        # reapply manifest if you see an error
        kustomize build apps/pipeline/upstream/env/aws | kubectl apply -f -

        # Katib
        kustomize build apps/katib/upstream/installs/katib-external-db-with-kubeflow | kubectl apply -f -

        # Configured for AWS Cognito
        
        # Ingress
        kustomize build distributions/aws/istio-ingress/overlays/cognito | kubectl apply -f -

        # ALB controller
        kustomize build distributions/aws/aws-alb-ingress-controller/base | kubectl apply -f -        

        # Envoy filter
        kustomize build distributions/aws/aws-istio-envoy-filter/base | kubectl apply -f -        
        ```
1. Follow the rest of the cognito guide from [section 5.0(Updating the domain with ALB address)](../cognito/README.md#50-updating-the-domain-with-ALB-address) to:
    1. Add/Update the DNS records in custom domain with the ALB address
    1. Create a profile for a user from the Cognito user pool
    1. Connect to the central dashboard
