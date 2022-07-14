## Why you should use Prometheus with Amazon Managed Service for Prometheus (AMP)
Many Kubeflow users utilize Prometheus and Grafana to monitor and visualize their metrics. However it can be difficult to scale open source Prometheus and Grafana as the number of nodes to be monitored increases. AMP seeks to remedy this hardship by allowing multiple Prometheus servers to aggregate their metrics in Amazon Managed Prometheus, and finally Amazon Managed Grafana allows customers to then view these aggregated metrics.

## Steps to Setup Prometheus and AMP
1. Export cluster name and region as environment variables:
    1. `export CLUSTER_NAME=<your-cluster-name>`
    2. `export CLUSTER_REGION=<your-cluster-region>`
    3. Make sure to replace the following in the above commands:
        * **\<your-cluster-name\>**
        * **\<your-cluster-region\>**
2. Create an IAM Policy:
    1. `export AMP_POLICY_NAME=<desired-amp-policy-name>`
    2. Make sure to replace the following in the above command:
        * **\<desired-amp-policy-name\>** - a policy name of your choosing
    3. `export AMP_POLICY_ARN=$(aws iam create-policy --policy-name $AMP_POLICY_NAME --policy-document file://deployments/add-ons/prometheus/AMPIngestPermissionPolicy.json --query 'Policy.Arn' | tr -d '"')`
3. Create a Service Account:
    1. `eksctl create iamserviceaccount --name amp-iamproxy-ingest-service-account --namespace monitoring --cluster $CLUSTER_NAME --attach-policy-arn $POLICY_ARN --override-existing-serviceaccounts --approve —region $CLUSTER_REGION`
4. Create an AMP Workspace:
    1. `export AMP_WORKSPACE_ALIAS=<desired-amp-workspace-alias>`
    2. Make sure to replace the following in the above command:
        * **\<desired-workspace-alias\>** - a workspace alias of your choosing
    3. `export AMP_WORKSPACE_ARN=$(aws amp create-workspace —alias $AMP_WORKSPACE_ALIAS —query arn | tr -d '"')`
    4. `export AMP_WORKSPACE_REGION=$(echo $AMP_WORKSPACE_ARN | cut -d':' -f4)`
    5. `export AMP_WORKSPACE_ID=$(echo $AMP_WORKSPACE_ARN | cut -d':' -f6 | cut -d'/' -f2)`
5. Edit deployments/add-ons/prometheus/params.env:
    1. ```
       workspaceRegion=<your-workspace-region>
       workspaceId=<your-workspace-id>
       ```
    2. Make sure to replace the following in the above lines:
        * **\<your-workspace-region\>** - Can be retrieved by:
            * `echo $AMP_WORKSPACE_REGION`
        * **\<your-workspace-id\>** - Can be retrieved by:
            * `echo $AMP_WORKSPACE_ID`
6. Create the monitoring namespace:
    1. `kubectl create namespace monitoring`
7. Run the kustomize build command to build your prometheus resources:
    1. `kustomize build deployments/add-ons/prometheus | kubectl apply -f`

## Steps to Verify Prometheus and AMP are Connected
1. Get the Prometheus Pod name:
    1. `export PROMETHEUS_POD_NAME=$(kubectl get pods --namespace=monitoring | grep "prometheus-deployment" | cut -d' ' -f1)`
2. Start port forwarding for the prometheus pod:
    1. `kubectl port-forward $PROMETHEUS_POD_NAME 9090:9090 --namespace=monitoring &`
3. Move into the tests directory:
    1. `cd tests`
5. Run the **check_AMP_connects_to_prometheus()** function (checks the KFP create experiment count):
    1. `python3 -c 'import os; import e2e.utils.prometheus.setup_prometheus_server as setup_prometheus_server; cluster_region = os.environ["CLUSTER_REGION"]; workspace_id = os.environ["AMP_WORKSPACE_ID"]; setup_prometheus_server.check_AMP_connects_to_prometheus(cluster_region, workspace_id, expected_value=0)'`
    2. If all is working, this should not trigger an assertion error.
