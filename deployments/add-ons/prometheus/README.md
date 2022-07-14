## Steps to setup Prometheus and Amazon Managed Service for Prometheus
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
    1. `workspaceRegion=<your-workspace-region>`
    2. `workspaceId=<your-workspace-id>`
    3. Make sure to replace the following in the above lines:
        * **\<your-workspace-region\>** - Can be retrieved by:
            * `echo $AMP_WORKSPACE_REGION`
        * **\<your-workspace-id\>** - Can be retrieved by:
            * `echo $AMP_WORKSPACE_ID`
6. Create the monitoring namespace:
    1. `kubectl create namespace monitoring`
7. Run the kustomize build command to build your prometheus resources:
    1. `kustomize build deployments/add-ons/prometheus | kubectl apply -f`
