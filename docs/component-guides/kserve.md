# Use S3 as storage Uri for KFServing/KServe
  
## Motivation  
When deploying a model server, you can specify in the `storageUri` the S3 path to your model.  
If the S3 bucket is private, KFServing/KServe will need to be authorized to download your model.  
To do so, we can leverage the fact that KFServing/KServe supports Kubernetes [Service Accounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/#:~:text=A%20service%20account%20provides%20an,recommended%20by%20the%20Kubernetes%20project.).  

## Overview  
The goal is to create a Service Account that has access to the bucket and then specify this Service Account in the inference service definition to allow KFServing/KServe to download the model.    
The Service Account will reference the secret with AWS credentials created during the installation of Kubeflow, more precisely, it will reference the secret `mlpipeline-minio-artifact` created by the Secrets Manager.  
  
## 1.0 Prerequisites  
  
1. The secrets were setup for the namespace you want to deploy your model. This can be done by following [this guide](./notebooks.md#setup-the-secrets-access)
  
## 2.0 Setup  
1. Create a Service Account definition that references the secret `mlpipeline-minio-artifact`  .  

**aws-service-account.yaml**  
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aws-sa
secrets:
- name: mlpipeline-minio-artifact  
```  

2. Apply the Service Account to the namespace you want to deploy your model to (eg: kubeflow-user-example-com).    
```
kubectl apply -f aws-service-account.yaml -n <YOUR_NAMESPACE>  
```  
For instance, if your namespace is `kubeflow-user-example-com`, then you would do the following :  
```
kubectl apply -f aws-service-account.yaml -n kubeflow-user-example-com  
```  
  
3. Specify the Service Account when deploying a model server  
This can be done by adding it to the `InferenceService` yaml definition :  
**sklearn_iris.yaml**
```yaml
apiVersion: "serving.kubeflow.org/v1beta1"
kind: "InferenceService"
metadata:
  name: "sklearn-iris"
spec:
  predictor:
    serviceAccountName: aws-sa
    sklearn:
      storageUri: <YOUR_S3_URI>  
```  
Here you would replace `<YOUR_S3_URI>` with your S3 uri (eg: s3://mybucket/mymodel)  
  
4. Deploy your model server  
Now you can deploy your model in your namespace.  
```
kubectl apply -f sklearn_iris.yaml -n <YOUR_NAMESPACE>
```  
  
5. Verify that your model was downloaded successfully  
The model server has a `storage-initializer` container that takes care of downloading the model.  
First check the name of the pod for your inference service.
```
kubectl get inferenceservice -n <YOUR_NAMESPACE>
```  
With the following command, we can check the logs of the `storage-initializer` after the deployment.
```
kubectl logs <YOUR_INFERENCE_SERVICE_POD> -n <YOUR_NAMESPACE> -c storage-initializer
```  
You should see a message saying the model was mounted successfully.