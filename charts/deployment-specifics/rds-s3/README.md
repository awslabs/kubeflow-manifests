[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/awslabs/kubeflow-manifests/issues)
![current development version](https://img.shields.io/badge/Kubeflow-v1.5.1-green.svg?style=flat)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
# Helm Installation for Kubeflow on AWS (RDS/S3)

## Overview
[Helm][] is the package manager for Kubernetes. In the following instructions, users can use **Helm** to install and manage **Kubeflow** instead of [Kustomize][].

## Install Helm
[Install Helm][] to you computer with one of the options you preferred. Check your helm version running:
```bash
helm version
```
Make sure you are using **helm v3.7+**.

## Prerequisites
Install required dependencies and create an EKS cluster following the [Prerequisite][] guideline. 

## RDS and S3 Installation
This guide describes how to deploy Kubeflow on AWS EKS using **RDS/S3** to persist KFP data. For advantage of using **RDS/S3**, refer to [existing installation guideline][] with kustomize.


Be sure that you have satisfied the [Installation Prerequisite][] before working through this guide.

Install helm through `helm install [Release Name] [Path]` command: 


## Automated Deployment Guide

1. Install Cert-Manager:

```bash
helm install cert-manager helm/common/cert-manager \
--namespace cert-manager \
--create-namespace \
--set installCRDs=true
```

Install [cmctl][] and verify the installation following [cert-manager Verification][]

Check if cmctl is ready:
```bash
$ cmctl check api
The cert-manager API is ready
```

Verify cert-manager pods are running:
```bash
$ kubectl get pods --namespace cert-manager

NAME                                       READY   STATUS    RESTARTS   AGE
cert-manager-5c6866597-zw7kh               1/1     Running   0          2m
cert-manager-cainjector-577f6d9fd7-tr77l   1/1     Running   0          2m
cert-manager-webhook-787858fcdb-nlzsq      1/1     Running   0          2m
```


2. Install Istio:
```bash
helm install istio-1-11 helm/common/istio-1-11
```

3. Install kubeflow namespace:
```bahs
helm install kubeflow-namespace helm/common/kubeflow-namespace
```


Follow [Step 2.1][] for AWS resources automated setup. The script takes care of creating the S3 bucket, creating the S3 Secrets using the Secrets manager, setting up the RDS database, and creating the RDS Secret using the Secrets manager. The script also edits the required configuration files for Kubeflow Pipelines to be properly configured for the RDS database during Kubeflow installation. The script also handles cases where the resources already exist. In this case, the script will simply skip the step.

```bash
export CLUSTER_REGION=
export CLUSTER_NAME=
export S3_BUCKET=
export MINIO_AWS_ACCESS_KEY_ID=
export MINIO_AWS_SECRET_ACCESS_KEY=
export RDS_SECRET_NAME=
export S3_SECRET_NAME=
export DB_INSTANCE_NAME=
export DB_SUBNET_GROUP_NAME=
```

```bash
cd tests/e2e
```

```bash
PYTHONPATH=.. python3 utils/rds-s3/auto-rds-s3-setup.py \
--region $CLUSTER_REGION --cluster $CLUSTER_NAME \
--bucket $S3_BUCKET --s3_secret_name $S3_SECRET_NAME \
--s3_aws_access_key_id $MINIO_AWS_ACCESS_KEY_ID \
--s3_aws_secret_access_key $MINIO_AWS_SECRET_ACCESS_KEY \
--db_instance_name $DB_INSTANCE_NAME --rds_secret_name $RDS_SECRET_NAME \
--db_subnet_group_name $DB_SUBNET_GROUP_NAME
```



4. Install Kubeflow Networking Components:

```bash
helm install kubeflow-roles helm/apps/kubeflow-roles;
helm install kubeflow-issuer helm/apps/kubeflow-issuer;
helm install kubeflow-istio-resources helm/apps/kubeflow-istio-resources;
helm install cluster-local-gateway helm/apps/cluster-local-gateway;
helm install knative-serving helm/apps/knative-serving;
helm install knative-eventing helm/apps/knative-eventing;
```


5. Install the rest of Kubeflow Components:
```bash
helm install dex helm/apps/dex;
helm install oidc-authservice helm/apps/oidc-authservice;
helm install aws-telemetry helm/apps/aws-telemetry;
helm install central-dashboard helm/apps/central-dashboard;
helm install training-operator helm/apps/training-operator;
helm install tensorboard-controller helm/apps/tensorboard-controller;
helm install tensorboards-web-app helm/apps/tensorboards-web-app;
helm install volumes-web-app helm/apps/volumes-web-app;
helm install jupyter-web-app helm/apps/jupyter-web-app;
helm install notebook-controller helm/apps/notebook-controller;
helm install models-web-app helm/apps/models-web-app;
helm install kserve helm/apps/kserve;
```

## [RDS and S3] Deploy both RDS and S3
6. Filled in parameters for **values.yaml** in the following charts: \
        -`helm/deployment-specifics/rds-s3/rds-and-s3/aws-secrets-manager/values.yaml` \
        -`helm/deployment-specifics/rds-s3/rds-and-s3/kubeflow-pipelines/values.yaml` \
You can file your rds-host end point from `awsconfigs/apps/pipeline/rds/params.env`

7. Configure for RDS and S3 to persist data: \
        - Install **Kubeflow-pipelines**, **Katib** and **AWS-Secrets-Manager** 
        
```bash
helm install kubeflow-pipelines helm/deployment-specifics/rds-s3/rds-and-s3/kubeflow-pipelines;
helm install katib helm/deployment-specifics/rds-s3/rds-and-s3/katib;
helm install aws-secrets-manager helm/deployment-specifics/rds-s3/rds-and-s3/aws-secrets-manager;
```

## [RDS Only] Deploy only with RDS
6. Filled in parameters for **values.yaml** in the following charts: \
        -`helm/deployment-specifics/rds-s3/rds-only/aws-secrets-manager/values.yaml` \
        -`helm/deployment-specifics/rds-s3/rds-only/kubeflow-pipelines/values.yaml` \
You can file your rds-host end point from `awsconfigs/apps/pipeline/rds/params.env`

7. Configure for RDS to persist data: \
        - Install **Kubeflow-pipelines**, **Katib** and **AWS-Secrets-Manager** 

```bash
helm install kubeflow-pipelines helm/deployment-specifics/rds-s3/rds-only/kubeflow-pipelines;
helm install katib helm/deployment-specifics/rds-s3/rds-only/katib;
helm install aws-secrets-manager helm/deployment-specifics/rds-s3/rds-only/aws-secrets-manager;
```

## [S3 Only] Deploy only with S3
6. Filled in parameters for **values.yaml** in the following charts: \
        -`helm/deployment-specifics/rds-s3/s3-only/aws-secrets-manager/values.yaml` \
        -`helm/deployment-specifics/rds-s3/s3-only/kubeflow-pipelines/values.yaml` \

7. Configure for S3 to persist data: \
        - Install **Kubeflow-pipelines** 

```bash
helm install kubeflow-pipelines helm/deployment-specifics/rds-s3/s3-only/kubeflow-pipelines;
helm install katib helm/apps/katib;
helm install aws-secrets-manager helm/deployment-specifics/rds-s3/s3-only/aws-secrets-manager;
```



8. Install **Admission Webhook** , **Profiles and Kubeflow Access-Management** and **User Namespace** 
```bash
helm install admission-webhook helm/apps/admission-webhook;
helm install profiles-and-kfam helm/apps/profiles-and-kfam;
helm install user-namespace helm/apps/user-namespace;
```


## Verify Installation

9. Your should see helm releases are in deployed status:



```bash
$ helm list -A
NAME                    	NAMESPACE   	REVISION	UPDATED                             	STATUS  	CHART                         	APP VERSION
admission-webhook       	default     	1       	2022-08-01 22:30:00.564628 -0700 PDT	deployed	admission-webhook-0.1.0       	1.16.0     
aws-secrets-manager     	default     	1       	2022-08-01 22:22:58.608745 -0700 PDT	deployed	aws-secrets-manager-0.1.0     	1.16.0     
aws-telemetry           	default     	1       	2022-08-01 17:21:10.195479 -0700 PDT	deployed	aws-telemetry-0.1.0           	1.16.0     
central-dashboard       	default     	1       	2022-08-01 17:21:21.310655 -0700 PDT	deployed	central-dashboard-0.1.0       	1.16.0     
cert-manager            	cert-manager	1       	2022-08-01 15:44:31.798334 -0700 PDT	deployed	cert-manager-v1.5.0           	v1.5.0     
cluster-local-gateway   	default     	1       	2022-08-01 17:16:15.751197 -0700 PDT	deployed	cluster-local-gateway-0.1.0   	1.16.0     
dex                     	default     	1       	2022-08-01 23:58:22.411183 -0700 PDT	deployed	dex-0.1.0                     	1.16.0     
istio-1-11              	default     	1       	2022-08-01 15:47:06.444182 -0700 PDT	deployed	istio-1-11-0.1.0              	1.16.0     
jupyter-web-app         	default     	1       	2022-08-01 17:23:32.396849 -0700 PDT	deployed	jupyter-web-app-0.1.0         	1.16.0     
katib                   	default     	1       	2022-08-01 17:33:01.807205 -0700 PDT	deployed	katib-0.1.0                   	1.16.0     
knative-eventing        	default     	1       	2022-08-01 17:18:20.486062 -0700 PDT	deployed	knative-eventing-0.1.0        	1.16.0     
knative-serving         	default     	1       	2022-08-01 17:16:45.779968 -0700 PDT	deployed	knative-serving-0.1.0         	1.16.0     
kserve                  	default     	1       	2022-08-01 17:24:54.159497 -0700 PDT	deployed	kserve-0.1.0                  	1.16.0     
kubeflow-issuer         	default     	1       	2022-08-01 17:15:49.128412 -0700 PDT	deployed	kubeflow-issuer-0.1.0         	1.16.0     
kubeflow-istio-resources	default     	1       	2022-08-01 17:15:59.03287 -0700 PDT 	deployed	kubeflow-istio-resources-0.1.0	1.16.0     
kubeflow-namespace      	default     	1       	2022-08-01 15:48:24.428391 -0700 PDT	deployed	kubeflow-namespace-0.1.0      	1.16.0     
kubeflow-pipelines      	default     	3       	2022-08-01 22:17:29.324491 -0700 PDT	deployed	kubeflow-pipelines-0.1.0      	1.16.0     
kubeflow-roles          	default     	1       	2022-08-01 17:15:29.553439 -0700 PDT	deployed	kubeflow-roles-0.1.0          	1.16.0     
models-web-app          	default     	1       	2022-08-01 17:24:28.610643 -0700 PDT	deployed	models-web-app-0.1.0          	1.16.0     
notebook-controller     	default     	1       	2022-08-01 17:23:58.231029 -0700 PDT	deployed	notebook-controller-0.1.0     	1.16.0     
oidc-authservice        	default     	1       	2022-08-01 23:50:10.332276 -0700 PDT	deployed	oidc-authservice-0.1.0        	1.16.0     
profiles-and-kfam       	default     	1       	2022-08-01 22:03:06.767057 -0700 PDT	deployed	profiles-and-kfam-0.1.0       	1.16.0     
tensorboard-controller  	default     	1       	2022-08-01 17:22:23.865719 -0700 PDT	deployed	tensorboard-controller-0.1.0  	1.16.0     
tensorboards-web-app    	default     	1       	2022-08-01 17:22:51.6382 -0700 PDT  	deployed	tensorboards-web-app-0.1.0    	1.16.0     
training-operator       	default     	1       	2022-08-01 17:21:54.888535 -0700 PDT	deployed	training-operator-0.1.0       	1.16.0     
user-namespace          	default     	1       	2022-08-01 22:03:33.013485 -0700 PDT	deployed	user-namespace-0.1.0          	1.16.0     
volumes-web-app         	default     	1       	2022-08-01 17:23:13.419332 -0700 PDT	deployed	volumes-web-app-0.1.0         	1.16.0    
```


10. Check all pods are running and ready:
```bash
NAMESPACE                   NAME                                                         READY   STATUS    RESTARTS   AGE
auth                        dex-5ddf47d88d-2s6ph                                         1/1     Running   1          101s
cert-manager                cert-manager-7c86cb795d-vtf9m                                1/1     Running   0          8h
cert-manager                cert-manager-cainjector-7c96bbd9f5-4gm7k                     1/1     Running   0          8h
cert-manager                cert-manager-webhook-f6648c54b-4mmjw                         1/1     Running   0          8h
istio-system                authservice-0                                                1/1     Running   0          49s
istio-system                cluster-local-gateway-64f58f66cb-lj4wp                       1/1     Running   0          6h43m
istio-system                istio-ingressgateway-8577c57fb6-kvlh6                        1/1     Running   0          8h
istio-system                istiod-6c86784695-nqktj                                      1/1     Running   0          8h
knative-eventing            eventing-controller-79895f9c56-zx6gr                         1/1     Running   0          6h40m
knative-eventing            eventing-webhook-78f897666-ljkp5                             1/1     Running   0          6h40m
knative-eventing            imc-controller-688df5bdb4-tsw5n                              1/1     Running   0          6h40m
knative-eventing            imc-dispatcher-646978d797-6stqx                              1/1     Running   0          6h40m
knative-eventing            mt-broker-controller-67c977497-xlg4g                         1/1     Running   0          6h40m
knative-eventing            mt-broker-filter-66d4d77c8b-g5898                            1/1     Running   0          6h40m
knative-eventing            mt-broker-ingress-5c8dc4b5d7-sfk58                           1/1     Running   0          6h40m
knative-serving             activator-7476cc56d4-ffhwg                                   2/2     Running   0          6h42m
knative-serving             autoscaler-5c648f7465-rwspb                                  2/2     Running   0          6h42m
knative-serving             controller-57c545cbfb-pt9n2                                  2/2     Running   0          6h42m
knative-serving             istio-webhook-578b6b7654-bnzx6                               2/2     Running   0          6h42m
knative-serving             networking-istio-6b88f745c-fk2wr                             2/2     Running   0          6h42m
knative-serving             webhook-6fffdc4d78-nwnmj                                     2/2     Running   0          6h42m
kserve                      kserve-controller-manager-0                                  2/2     Running   0          6h34m
kube-system                 aws-node-7vwj6                                               1/1     Running   0          8h
kube-system                 aws-node-g5m7x                                               1/1     Running   0          8h
kube-system                 aws-node-t6qlb                                               1/1     Running   0          8h
kube-system                 aws-node-wgw9r                                               1/1     Running   0          8h
kube-system                 aws-node-wkflw                                               1/1     Running   0          8h
kube-system                 coredns-86bcc74758-r9dkl                                     1/1     Running   0          8h
kube-system                 coredns-86bcc74758-x747p                                     1/1     Running   0          8h
kube-system                 csi-secrets-store-89p64                                      3/3     Running   0          7h54m
kube-system                 csi-secrets-store-cd4jd                                      3/3     Running   0          7h54m
kube-system                 csi-secrets-store-cjc97                                      3/3     Running   0          7h54m
kube-system                 csi-secrets-store-n9r7w                                      3/3     Running   0          7h54m
kube-system                 csi-secrets-store-provider-aws-58dn9                         1/1     Running   0          7h54m
kube-system                 csi-secrets-store-provider-aws-gddhm                         1/1     Running   0          7h54m
kube-system                 csi-secrets-store-provider-aws-ktsxw                         1/1     Running   0          7h54m
kube-system                 csi-secrets-store-provider-aws-l45cl                         1/1     Running   0          7h54m
kube-system                 csi-secrets-store-provider-aws-l4fv2                         1/1     Running   0          7h54m
kube-system                 csi-secrets-store-qtw9f                                      3/3     Running   0          7h54m
kube-system                 kube-proxy-45252                                             1/1     Running   0          8h
kube-system                 kube-proxy-dcth4                                             1/1     Running   0          8h
kube-system                 kube-proxy-qbz7z                                             1/1     Running   0          8h
kube-system                 kube-proxy-t2fh2                                             1/1     Running   0          8h
kube-system                 kube-proxy-wjd9h                                             1/1     Running   0          8h
kubeflow-user-example-com   ml-pipeline-ui-artifact-8dcf69986-4684q                      2/2     Running   0          116m
kubeflow-user-example-com   ml-pipeline-visualizationserver-7c8dfd5cb-r9q7v              2/2     Running   0          116m
kubeflow                    admission-webhook-deployment-7df7558c67-tcbch                1/1     Running   0          117m
kubeflow                    aws-secrets-sync-647d796d87-76v2m                            2/2     Running   0          97m
kubeflow                    cache-server-5bdbd59959-7fthm                                2/2     Running   0         6h27m
kubeflow                    centraldashboard-79f489b55-kc7m6                             2/2     Running   0          6h38m
kubeflow                    jupyter-web-app-deployment-7cd59c5c95-hhrt5                  1/1     Running   0          6h36m
kubeflow                    katib-controller-58ddb4b856-db7mb                            1/1     Running   0          6h26m
kubeflow                    katib-db-manager-7868dccc54-h9w8q                            1/1     Running   0          6h26m
kubeflow                    katib-ui-f787b9d88-9tbw6                                     1/1     Running   0          6h26m
kubeflow                    kserve-models-web-app-5c64c8d8bb-sgkw9                       2/2     Running   0          6h35m
kubeflow                    kubeflow-pipelines-profile-controller-84bcbdb899-tkdfm       1/1     Running   0          6h27m
kubeflow                    metacontroller-0                                             1/1     Running   0          6h27m
kubeflow                    metadata-envoy-deployment-86d856fc6-6dnqq                    1/1     Running   0          6h27m
kubeflow                    metadata-grpc-deployment-f8d68f687-vkz2c                     2/2     Running   0         6h27m
kubeflow                    metadata-writer-d7ff8d4bc-bm5ml                              2/2     Running   0         6h27m
kubeflow                    minio-5b65df66c9-dpl8g                                       2/2     Running   0          6h27m
kubeflow                    ml-pipeline-777648985d-sdjdn                                 2/2     Running   0         6h27m
kubeflow                    ml-pipeline-persistenceagent-7bf47b869c-9r7cg                2/2     Running   0          6h27m
kubeflow                    ml-pipeline-scheduledworkflow-565fd7846-lqhwv                2/2     Running   0          6h27m
kubeflow                    ml-pipeline-ui-6c8b78ccd8-dqk7d                              2/2     Running   0          6h27m
kubeflow                    ml-pipeline-viewer-crd-68bcdc87f9-48z5f                      2/2     Running   1          6h27m
kubeflow                    ml-pipeline-visualizationserver-7bc59978d-gtslv              2/2     Running   0          6h27m
kubeflow                    notebook-controller-deployment-7474fbff66-8zgkc              2/2     Running   1          6h35m
kubeflow                    profiles-deployment-5cc86bc965-jn7gc                         3/3     Running   1          116m
kubeflow                    tensorboard-controller-controller-manager-5cbddb7fb5-2l6gv   3/3     Running   1          6h37m
kubeflow                    tensorboards-web-app-deployment-7c5db448d7-g7ltm             1/1     Running   0          6h37m
kubeflow                    training-operator-6bfc7b8d86-jccv6                           1/1     Running   0          6h38m
kubeflow                    volumes-web-app-deployment-87484c848-cm786                   1/1     Running   0          6h36m
kubeflow                    workflow-controller-5cb67bb9db-5m4wb                         2/2     Running   0          6h27m
```


9. Verify the installation following (https://awslabs.github.io/kubeflow-manifests/docs/deployment/rds-s3/guide/#40-verify-the-installation)

10. Port-forward into Kubeflow Dashboard
```bash
kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is [licensed](LICENSE) under the Apache-2.0 License.


[Helm]: https://helm.sh/
[Kustomize]: https://kustomize.io/
[Install Helm]: https://helm.sh/docs/intro/install/
[Prerequisite]: https://awslabs.github.io/kubeflow-manifests/docs/deployment/prerequisites/
[cert-manager Verification]: https://cert-manager.io/docs/installation/verify/#check-cert-manager-api
[cmctl]: https://cert-manager.io/docs/usage/cmctl/#installation
[existing installation guideline]: https://awslabs.github.io/kubeflow-manifests/docs/deployment/rds-s3/guide/
[Step 2.1]: https://awslabs.github.io/kubeflow-manifests/docs/deployment/rds-s3/guide/#21-option-1-automated-setup