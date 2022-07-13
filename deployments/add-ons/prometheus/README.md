## Steps to setup Prometheus and Amazon Managed Service for Prometheus
1. Create an IAM Policy:
    1. `aws iam create-policy —policy-name AMPIngestPolicy —policy-document file://deployments/add-ons/prometheus/AMPIngestPermissionPolicy.json`
    2. You will need to copy the ARN, as you will need to use it in the next command replacing <your-policy-arn>
2. Create a Service Account:
    1. `eksctl create iamserviceaccount --name amp-iamproxy-ingest-service-account --role-name <your-role-name> --namespace monitoring --cluster \
<your-cluster-name> --attach-policy-arn <your-policy-arn> --override-existing-serviceaccounts --approve --region <your-cluster-region>`
    2. Make sure to replace the following in the above command:
        * **\<your-role-name\>** - a role name of your choosing
        * **\<your-cluster-name\>**
        * **\<your-policy-arn\>** - from step 1
        * **\<your-cluster-region\>**
3. Create an AMP Workspace:
    1. `aws amp create-workspace --alias <your-workspace-alias>`
    2. Make sure to replace the following in the above command:
        * **\<your-workspace-alias\>** - a workspace alias of your choosing
    3. You will need to copy the workspace ID of this AMP Workspace (which can be printed out to the command line.)
4. Edit deployments/add-ons/prometheus/params.env:
    1. `workspaceRegion=<your-workspace-region>`
    2. `workspaceId=<your-workspace-id>`
    3. Make sure to replace the following in the above lines:
        * **\<your-workspace-region\>**
        * **\<your-workspace-id\>** - from step 3
5. Create the monitoring namespace:
    1. `kubectl create namespace monitoring`
6. Run the kustomize build command to build your prometheus resources:
    1. `kustomize build deployments/add-ons/prometheus | kubectl apply -f`
