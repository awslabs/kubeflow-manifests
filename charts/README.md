[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/awslabs/kubeflow-manifests/issues)
![current development version](https://img.shields.io/badge/Kubeflow-v1.5.1-green.svg?style=flat)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
# Helm Installation for Kubeflow on AWS (Vanilla)

## Overview
[Helm][] is the package manager for Kubernetes. In the following instructions, users can use **Helm** to install and manage **Kubeflow** instead of [Kustomize][].

## Install Helm
[Install Helm][] to your computer with one of the options you preferred. Check your helm version running:
```bash
helm version
```
Make sure you are using **helm v3.7+**.

## Prerequisites
Install required dependencies and create an EKS cluster following the [Installation Prerequisite][] guideline. 

## Vanilla Installation
This guide describes how to deploy Kubeflow on AWS EKS with **Helm**. This vanilla version has minimal changes to the upstream Kubeflow manifests.

Be sure that you have satisfied the [Installation Prerequisite][] before working through this guide.

Install helm through `helm install [Release Name] [Path]` command: 


1. Install Cert-Manager and Kubeflow-roles:

```bash
helm install cert-manager charts/common/cert-manager \
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

``bash
helm install kubeflow-roles charts/common/kubeflow-roles;
```

2. Install Istio and Kubeflow-issuer:
```bash
helm install istio-1-14 charts/common/istio-1-14;
helm install kubeflow-issuer charts/common/kubeflow-issuer;
```

3. Install Kubeflow Namespace, dex, knative
```bash
helm install kubeflow-namespace charts/common/kubeflow-namespace;
helm install dex charts/common/dex;
helm install cluster-local-gateway charts/common/cluster-local-gateway;
helm install knative-serving charts/common/knative-serving;
helm install knative-eventing charts/common/knative-eventing;
```

4. Install OIDC-authservice, kubeflow-istio-resources, and Kserve:

```bash
helm install oidc-authservice charts/common/oidc-authservice;
helm install kubeflow-istio-resources charts/common/kubeflow-istio-resources;
helm install kserve charts/common/kserve;
```

5. Install Kubeflow Components and profiles-and-kfam:

```bash
helm install admission-webhook charts/common/admission-webhook;
helm install profiles-and-kfam charts/common/profiles-and-kfam;
helm install aws-telemetry charts/common/aws-telemetry;
helm install central-dashboard charts/apps/central-dashboard;
helm install training-operator charts/apps/training-operator;
helm install tensorboard-controller charts/apps/tensorboard-controller;
helm install tensorboards-web-app charts/apps/tensorboards-web-app;
helm install volumes-web-app charts/apps/volumes-web-app;
helm install jupyter-web-app charts/apps/jupyter-web-app;
helm install notebook-controller charts/apps/notebook-controller;
helm install katib charts/apps/katib;
helm install models-web-app charts/apps/models-web-app;
helm install kubeflow-pipelines charts/apps/kubeflow-pipelines
```

6. Install user-namespace
```bash
helm install user-namespace charts/common/user-namespace;
```

## Connect to your Kubeflow cluster 
After installation, it will take some time for all Pods to become ready. Make sure all Pods are ready before trying to connect, otherwise you might get unexpected errors. To check that all Kubeflow-related Pods are ready, use the following commands:

```bash
kubectl get pods -n cert-manager
kubectl get pods -n istio-system
kubectl get pods -n auth
kubectl get pods -n knative-eventing
kubectl get pods -n knative-serving
kubectl get pods -n kubeflow
kubectl get pods -n kubeflow-user-example-com
# Depending on your installation if you installed KServe
kubectl get pods -n kserve
```

Your should see helm releases are in deployed status:
```bash
$ helm list --namespace cert-manager
NAME        	NAMESPACE   	REVISION	UPDATED                            	STATUS  	CHART              	APP VERSION
cert-manager	cert-manager	1       	2022-07-28 12:05:28.69295 -0700 PDT	deployed	cert-manager-v1.5.0	v1.5.0     
```

```bash
$ helm list
NAME                    	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART                         	APP VERSION
admission-webhook       	default  	1       	2022-07-28 12:57:27.613949 -0700 PDT	deployed	admission-webhook-0.1.0       	1.16.0     
aws-secrets-manager     	default  	1       	2022-07-28 12:55:30.291808 -0700 PDT	deployed	aws-secrets-manager-0.1.0     	1.16.0     
aws-telemetry           	default  	1       	2022-07-28 12:39:24.261685 -0700 PDT	deployed	aws-telemetry-0.1.0           	1.16.0     
central-dashboard       	default  	1       	2022-07-28 12:39:41.64472 -0700 PDT 	deployed	central-dashboard-0.1.0       	1.16.0     
cluster-local-gateway   	default  	1       	2022-07-28 12:31:55.501454 -0700 PDT	deployed	cluster-local-gateway-0.1.0   	1.16.0     
dex                     	default  	1       	2022-07-28 12:38:35.15731 -0700 PDT 	deployed	dex-0.1.0                     	1.16.0     
istio-1-11              	default  	1       	2022-07-28 12:07:47.921271 -0700 PDT	deployed	istio-1-11-0.1.0              	1.16.0     
jupyter-web-app         	default  	1       	2022-07-28 12:42:23.163274 -0700 PDT	deployed	jupyter-web-app-0.1.0         	1.16.0     
katib                   	default  	1       	2022-07-28 12:54:47.810424 -0700 PDT	deployed	katib-0.1.0                   	1.16.0     
knative-eventing        	default  	1       	2022-07-28 12:34:36.922185 -0700 PDT	deployed	knative-eventing-0.1.0        	1.16.0     
knative-serving         	default  	1       	2022-07-28 12:32:33.226445 -0700 PDT	deployed	knative-serving-0.1.0         	1.16.0     
kserve                  	default  	1       	2022-07-28 12:44:00.152331 -0700 PDT	deployed	kserve-0.1.0                  	1.16.0     
kubeflow-issuer         	default  	1       	2022-07-28 12:31:22.068229 -0700 PDT	deployed	kubeflow-issuer-0.1.0         	1.16.0     
kubeflow-istio-resources	default  	1       	2022-07-28 12:31:40.286801 -0700 PDT	deployed	kubeflow-istio-resources-0.1.0	1.16.0     
kubeflow-namespace      	default  	1       	2022-07-28 12:09:07.416695 -0700 PDT	deployed	kubeflow-namespace-0.1.0      	1.16.0     
kubeflow-pipelines      	default  	1       	2022-07-28 12:51:57.293078 -0700 PDT	deployed	kubeflow-pipelines-0.1.0      	1.16.0     
kubeflow-roles          	default  	1       	2022-07-28 12:31:03.351416 -0700 PDT	deployed	kubeflow-roles-0.1.0          	1.16.0     
models-web-app          	default  	1       	2022-07-28 12:43:29.275867 -0700 PDT	deployed	models-web-app-0.1.0          	1.16.0     
notebook-controller     	default  	1       	2022-07-28 12:42:58.397411 -0700 PDT	deployed	notebook-controller-0.1.0     	1.16.0     
oidc-authservice        	default  	1       	2022-07-28 12:39:01.325914 -0700 PDT	deployed	oidc-authservice-0.1.0        	1.16.0     
profiles-and-kfam       	default  	1       	2022-07-28 12:58:02.22225 -0700 PDT 	deployed	profiles-and-kfam-0.1.0       	1.16.0     
tensorboard-controller  	default  	1       	2022-07-28 12:40:59.266969 -0700 PDT	deployed	tensorboard-controller-0.1.0  	1.16.0     
tensorboards-web-app    	default  	1       	2022-07-28 12:41:26.352725 -0700 PDT	deployed	tensorboards-web-app-0.1.0    	1.16.0     
training-operator       	default  	1       	2022-07-28 12:40:25.528385 -0700 PDT	deployed	training-operator-0.1.0       	1.16.0     
user-namespace          	default  	1       	2022-07-28 12:58:32.830817 -0700 PDT	deployed	user-namespace-0.1.0          	1.16.0     
volumes-web-app         	default  	1       	2022-07-28 12:41:57.884204 -0700 PDT	deployed	volumes-web-app-0.1.0         	1.16.0  
```

Check all Pods are running:

```bash
$ kubectl get pods -A
NAMESPACE                   NAME                                                         READY   STATUS    RESTARTS   AGE
auth                        dex-5ddf47d88d-6zdkk                                         1/1     Running   1          13h
cert-manager                cert-manager-7c86cb795d-62dn5                                1/1     Running   0          13h
cert-manager                cert-manager-cainjector-7c96bbd9f5-h5v9p                     1/1     Running   0          13h
cert-manager                cert-manager-webhook-f6648c54b-cx7f2                         1/1     Running   0          13h
istio-system                authservice-0                                                1/1     Running   0          13h
istio-system                cluster-local-gateway-64f58f66cb-vjd2c                       1/1     Running   0          12h
istio-system                istio-ingressgateway-8577c57fb6-tnfd4                        1/1     Running   0          13h
istio-system                istiod-6c86784695-skx7x                                      1/1     Running   0          13h
knative-eventing            eventing-controller-79895f9c56-78b7s                         1/1     Running   0          12h
knative-eventing            eventing-webhook-78f897666-r28ll                             1/1     Running   0          12h
knative-eventing            imc-controller-688df5bdb4-hsdv9                              1/1     Running   0          12h
knative-eventing            imc-dispatcher-646978d797-xcchg                              1/1     Running   0          12h
knative-eventing            mt-broker-controller-67c977497-bc4nr                         1/1     Running   0          12h
knative-eventing            mt-broker-filter-66d4d77c8b-qz559                            1/1     Running   0          12h
knative-eventing            mt-broker-ingress-5c8dc4b5d7-59ttr                           1/1     Running   0          12h
knative-serving             activator-7476cc56d4-cf2kr                                   2/2     Running   0          12h
knative-serving             autoscaler-5c648f7465-56dmm                                  2/2     Running   0          12h
knative-serving             controller-57c545cbfb-q676h                                  2/2     Running   0          12h
knative-serving             istio-webhook-578b6b7654-d8m57                               2/2     Running   0          12h
knative-serving             networking-istio-6b88f745c-gmqjx                             2/2     Running   0          12h
knative-serving             webhook-6fffdc4d78-qrht6                                     2/2     Running   0          12h
kserve                      kserve-controller-manager-0                                  2/2     Running   0          11h
kube-system                 aws-node-25jbk                                               1/1     Running   0          20h
kube-system                 aws-node-27fsc                                               1/1     Running   1          20h
kube-system                 aws-node-qdppn                                               1/1     Running   0          20h
kube-system                 aws-node-r6nll                                               1/1     Running   0          20h
kube-system                 aws-node-sqwp5                                               1/1     Running   0          20h
kube-system                 coredns-85d5b4454c-74trc                                     1/1     Running   0          20h
kube-system                 coredns-85d5b4454c-kjlq9                                     1/1     Running   0          20h
kube-system                 kube-proxy-2gtsm                                             1/1     Running   0          20h
kube-system                 kube-proxy-rkxzl                                             1/1     Running   0          20h
kube-system                 kube-proxy-wjx7w                                             1/1     Running   0          20h
kube-system                 kube-proxy-wsdhz                                             1/1     Running   0          20h
kube-system                 kube-proxy-x7lqs                                             1/1     Running   0          20h
kubeflow-user-example-com   ml-pipeline-ui-artifact-8dcf69986-chqvn                      2/2     Running   0          2m17s
kubeflow-user-example-com   ml-pipeline-visualizationserver-7c8dfd5cb-8hw5h              2/2     Running   0          2m17s
kubeflow                    admission-webhook-deployment-7df7558c67-hd7vh                1/1     Running   0          11h
kubeflow                    cache-server-5bdbd59959-pfz6k                                2/2     Running   0          12h
kubeflow                    centraldashboard-79f489b55-t6bt7                             2/2     Running   0          11h
kubeflow                    jupyter-web-app-deployment-7cd59c5c95-s6v7x                  1/1     Running   0          41m
kubeflow                    katib-controller-58ddb4b856-vpjjn                            1/1     Running   0          11h
kubeflow                    katib-db-manager-d77c6757f-cnt6m                             1/1     Running   0          11h
kubeflow                    katib-mysql-7894994f88-sq7st                                 1/1     Running   0          11h
kubeflow                    katib-ui-f787b9d88-s9jdp                                     1/1     Running   0          11h
kubeflow                    kserve-models-web-app-5c64c8d8bb-dpv5t                       2/2     Running   0          11h
kubeflow                    kubeflow-pipelines-profile-controller-84bcbdb899-tst5c       1/1     Running   0          12h
kubeflow                    metacontroller-0                                             1/1     Running   0          12h
kubeflow                    metadata-envoy-deployment-86d856fc6-zggtc                    1/1     Running   0          12h
kubeflow                    metadata-grpc-deployment-f8d68f687-qlpcd                     2/2     Running   3          12h
kubeflow                    metadata-writer-d7ff8d4bc-nzczk                              2/2     Running   0          12h
kubeflow                    minio-5b65df66c9-6c2r9                                       2/2     Running   0          12h
kubeflow                    ml-pipeline-7499f55b46-dkrmj                                 2/2     Running   1          12h
kubeflow                    ml-pipeline-persistenceagent-7bf47b869c-tgrbm                2/2     Running   0          12h
kubeflow                    ml-pipeline-scheduledworkflow-565fd7846-cvhvm                2/2     Running   0          12h
kubeflow                    ml-pipeline-ui-77477f77dc-m4n2f                              2/2     Running   0          12h
kubeflow                    ml-pipeline-viewer-crd-68bcdc87f9-8lxfm                      2/2     Running   1          12h
kubeflow                    ml-pipeline-visualizationserver-7bc59978d-28k9z              2/2     Running   0          12h
kubeflow                    mysql-f7b9b7dd4-7pz6x                                        2/2     Running   0          12h
kubeflow                    notebook-controller-deployment-7474fbff66-tnv4d              2/2     Running   1          43m
kubeflow                    profiles-deployment-5cc86bc965-c6rjl                         3/3     Running   1          39m
kubeflow                    tensorboard-controller-controller-manager-5cbddb7fb5-bsstp   3/3     Running   1          34m
kubeflow                    tensorboards-web-app-deployment-7c5db448d7-p46vn             1/1     Running   0          33m
kubeflow                    training-operator-6bfc7b8d86-9ps7z                           1/1     Running   0          11m
kubeflow                    volumes-web-app-deployment-87484c848-d4j9t                   1/1     Running   0          37m
kubeflow                    workflow-controller-5cb67bb9db-2xm5m                         2/2     Running   1          12h
```




## Port-Forward
Follow the following port-forward guideline to access Kubeflow (https://awslabs.github.io/kubeflow-manifests/docs/deployment/vanilla/guide/#port-forward)


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is [licensed](LICENSE) under the Apache-2.0 License.


[Helm]: https://helm.sh/
[Kustomize]: https://kustomize.io/
[Install Helm]: https://helm.sh/docs/intro/install/
[Installation Prerequisite]: https://awslabs.github.io/kubeflow-manifests/docs/deployment/prerequisites/
[cert-manager Verification]: https://cert-manager.io/docs/installation/verify/#check-cert-manager-api
[cmctl]: https://cert-manager.io/docs/usage/cmctl/#installation