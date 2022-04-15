# Notebooks Component Guide for Kubeflow on AWS

## Setup RDS & S3 credentials access for notebooks & pipelines
### Use Cases
- Be able to use `boto3` or aws libraries that require to pass in credentials in a notebook and specify credentials without hard coding them. Access the credentials via environment variables.  
- Be able to use [ml-metadata](https://github.com/google/ml-metadata/blob/master/g3doc/get_started.md) in a notebook (eg: to explore metadata) and specify the credentials needed by using environment variables.
- Be able to use [ml-metadata](https://github.com/google/ml-metadata/blob/master/g3doc/get_started.md) to query metadata during a pipeline run by passing a kubernetes secret to a pipeline component.  
- Be able to use `boto3` or aws libraries that require to pass in credentials in a Kubeflow Pipeline Component. 

The following script creates a kubernetes `mysql-secret` and `mlpipeline-minio-artifact` secrets with RDS & S3 credentials specified in AWS Secrets Manager created while deploying the platform. This is a sample for demonstrating how you can use [`PodDefault` resource](https://github.com/kubeflow/kubeflow/blob/master/components/admission-webhook/README.md) and secrets in Notebooks to access the metadata database and and artifacts in S3 bucket created by pipelines. Make sure you create separate database and IAM users and corresponding secrets in Secrets Manager for your users if you want fine grain access control and auditing.  

### Setup the secrets access
1. Navigate inside the script directory.
```
cd ../../tests/e2e
```
2. Install the script dependencies.
```shell
pip install -r requirements.txt
```
3. Execute the script, replace `YOUR_CLUSTER_REGION`, `YOUR_CLUSTER_NAME` and `YOUR_NAMESPACE` with the appropriate values.  
Note that `YOUR_NAMESPACE` represents the namespace the secrets will be setup for.  
For instance if your notebooks and pipelines will be in `kubeflow-user-example-com`, then you would use `kubeflow-user-example-com` in place of `YOUR_NAMESPACE`.
```shell
PYTHONPATH=.. python utils/notebooks/setup_secrets_access.py --region YOUR_CLUSTER_REGION --cluster YOUR_CLUSTER_NAME --profile-namespace YOUR_NAMESPACE
```  
You can always do `PYTHONPATH=.. python utils/notebooks/setup_secrets_access.py --help` to learn more about the parameters available.    

**Note :** The namespace must exist before executing the script.   

### (Optional) Set PodDefault selected by default in notebook UI  
The Kubeflow notebook UI allows to select credentials configurations when creating a notebook, by default no configuration is selected but we can add the `PodDefault` label created in the previous step to the list of selected configuration.  
This results in having the `PodDefault` already selected when creating a new notebook, otherwise the user must select it manually in the notebook UI.  
You can learn more about Kubeflow Notebooks [here](https://www.kubeflow.org/docs/components/notebooks/quickstart-guide/#detailed-steps)
  
**Important Note :**
Making this configuration default will introduce a dependency for the secrets and PodDefault to be available in all profile namespaces. Profile namespaces which do not have this resource will see failure in new notebook server creation if this PodDefault is not created.

This change can be done before or after installing Kubeflow, here is how to make this modification depending on these 2 options.  

#### **Option 1: Update notebook UI config before installing Kubeflow**
Modify the file `awsconfigs/apps/jupyter-web-app/configs/spawner_ui_config.yaml`
```yaml
  configurations:
    # List of labels to be selected, these are the labels from PodDefaults
    value:
      - add-aws-secret
```  
#### **Option 2: Update notebook UI config after installing Kubeflow**  
We can update the notebook UI config at runtime by using the following command :  
```shel
kubectl edit $(kubectl get cm -n kubeflow -l app=jupyter-web-app -o=name | grep 'web-app-config') -n kubeflow
```  

Modify the configuration :  
```yaml
  configurations:
    # List of labels to be selected, these are the labels from PodDefaults
    value:
      - add-aws-secret
```  
  
Once you are done making the changes you can save and exit your editor and restart the notebook deployment to apply the changes.   

```shell
kubectl rollout restart deployment jupyter-web-app-deployment -n kubeflow
```
### Verify notebook credentials configuration  
To verify that your `PodDefault` setup was done successfully, navigate to the notebook creation UI and make sure you can select the `PodDefault`.  
![](https://user-images.githubusercontent.com/26939775/155630906-0eecf1d9-3fb1-4d01-a85e-1cff46dc37e9.png)  
Then create a notebook and check that the environment variables are accessible :  
```python
import os

print(os.environ['port'])
```  


## AWS IAM for Kubeflow Profiles in Notebooks

### Use Cases

Access AWS resources through notebooks without exposing credentials.

### Configuration

Prerequisites for setting up AWS IAM for Kubeflow Profiles can be found [here](../../../profile-iam). The prerequisite steps will go through creating a profile that uses the `AwsIamForServiceAccount` plugin.

No additional configuration steps are required.

### Try It Out
1. Create a notebook server through the central dashboard.
1. Select the profile name from the top left drop down menu for the profile you created.
1. Create a notebook from [the sample](./samples/notebooks/verify_profile_iam_notebook.ipynb).
1. Run the notebook, it should be able to list the S3 buckets present in your account.
