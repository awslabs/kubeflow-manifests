+++
title = "Prometheus"
description = "Use Prometheus, Amazon Managed Service for Prometheus, and Amazon Managed Grafana to monitor metrics with Kubeflow on AWS"
weight = 5
+++

This guide shows how to setup a Prometheus server and an AMP workspace. It also shows to validate the correctness of this setup.

## Why you should use Prometheus with Amazon Managed Service for Prometheus (AMP)
Many Kubeflow users utilize Prometheus and Grafana to monitor and visualize their metrics. However it can be difficult to scale open source Prometheus and Grafana as the number of nodes to be monitored increases. AMP seeks to simplify this issue by allowing multiple Prometheus servers to aggregate their metrics in Amazon Managed Prometheus, and finally Amazon Managed Grafana allows customers to then view these aggregated metrics.

## Prerequisites
Download one of our deployment options by following the directions at: https://awslabs.github.io/kubeflow-manifests/docs/deployment/

**Note:** The steps below will assume you are sitting in the kubeflow-manifests directory.

## Steps to Setup Prometheus and AMP
1. Export cluster name and region as environment variables:
    1. Make sure to replace the following in the below commands:
        * **\<your-cluster-name\>**
        * **\<your-cluster-region\>**
    2. ```bash
       export CLUSTER_NAME=<your-cluster-name>
       ```
    3. ```bash
       export CLUSTER_REGION=<your-cluster-region>
       ```
2. Create an IAM Policy:
    1. Make sure to replace the following in the below command:
        * **\<desired-amp-policy-name\>** - a policy name of your choosing
    2. ```bash
       export AMP_POLICY_NAME=<desired-amp-policy-name>
       ```
    3. ```bash
       export AMP_POLICY_ARN=$(aws iam create-policy --policy-name $AMP_POLICY_NAME --policy-document file://deployments/add-ons/prometheus/AMPIngestPermissionPolicy.json --query 'Policy.Arn' | tr -d '"')
       ```
3. Create a Service Account:
    1. ```bash
       eksctl create iamserviceaccount --name amp-iamproxy-ingest-service-account --namespace monitoring --cluster $CLUSTER_NAME --attach-policy-arn $AMP_POLICY_ARN --override-existing-serviceaccounts --approve --region $CLUSTER_REGION
       ```
4. Create an AMP Workspace:
    1. Make sure to replace the following in the below command:
        * **\<desired-workspace-alias\>** - a workspace alias of your choosing
    2. ```bash
       export AMP_WORKSPACE_ALIAS=<desired-amp-workspace-alias>
       ```
    3. ```bash
       export AMP_WORKSPACE_ARN=$(aws amp create-workspace --region $CLUSTER_REGION --alias $AMP_WORKSPACE_ALIAS --query arn | tr -d '"')
       ```
    4. ```bash
       export AMP_WORKSPACE_REGION=$(echo $AMP_WORKSPACE_ARN | cut -d':' -f4)
       ```
    5. ```bash
       export AMP_WORKSPACE_ID=$(echo $AMP_WORKSPACE_ARN | cut -d':' -f6 | cut -d'/' -f2)
       ```
5. Update deployments/add-ons/prometheus/params.env with your workspace id and region:
    1. ```bash
       pushd tests; python3 -c 'import os; import e2e.utils.prometheus.setup_prometheus_server as setup_prometheus_server; region = os.environ["AMP_WORKSPACE_REGION"]; workspace_id = os.environ["AMP_WORKSPACE_ID"]; local_prometheus_port = os.environ["LOCAL_PROMETHEUS_PORT"]; setup_prometheus_server.update_params_env(workspace_id, region, params_env_file_path="../deployments/add-ons/prometheus/params.env")'; popd
       ```
6. Run the kustomize build command to build your prometheus resources:
    1. ```bash
       kustomize build deployments/add-ons/prometheus | kubectl apply -f -
       ```

## Steps to Verify Prometheus and AMP are Connected
1. Make sure you have awscurl installed:
    1. ```bash
       pip3 install awscurl
       ```
2. Start port-forwarding for the prometheus pod:
    1. Make sure to replace the following in the below command:
        * **\<desired-local-port\>** - a workspace alias of your choosing
    2. ```bash
       export LOCAL_PROMETHEUS_PORT=<desired-local-port>
       ```
    3. ```bash
       kubectl port-forward $(kubectl get pods --namespace=monitoring | grep "prometheus-deployment" | cut -d' ' -f1) $LOCAL_PROMETHEUS_PORT:9090 --namespace=monitoring &
       ```
3. Make sure your credentials are in ~/.aws/credentials:
    1. ```bash
       aws configure
       ```
4. Run the below command to verify the KFP create experiment count metric is being correctly exported to AMP:
    1. ```bash
       pushd tests; python3 -c 'import os; import e2e.utils.prometheus.setup_prometheus_server as setup_prometheus_server; cluster_region = os.environ["CLUSTER_REGION"]; workspace_id = os.environ["AMP_WORKSPACE_ID"]; setup_prometheus_server.local_prometheus_port = os.environ["LOCAL_PROMETHEUS_PORT"]; setup_prometheus_server.check_AMP_connects_to_prometheus(cluster_region, workspace_id, expected_value=0)'; popd
       ```
    2. If all is working, this should not trigger an assertion error.
5. Get the PID and kill the port-forwarding process:
    1. ```bash
       export PORT_FORWARDING_PROCESS=$(lsof -i :$LOCAL_PROMETHEUS_PORT | sed -n 2p | cut -d' ' -f2)
       ```
    2. ```bash
       kill $PORT_FORWARDING_PROCESS
       ```
