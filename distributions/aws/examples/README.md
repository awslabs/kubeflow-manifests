# Kubeflow on AWS
## Deployment Options

In this directory you can find instructions for deploying Kubeflow on Amazon Elastic Kubernetes Service (Amazon EKS). Depending upon your use case you may choose to integrate your deployment with different AWS services. Following are various deployment options:

### Components configured for RDS and S3
Installation steps can be found [here](rds-s3)

### Components configured for Cognito
Installation steps can be found [here](cognito)

### Components configured for Cognito, RDS and S3
Installation steps can be found [here](cognito-rds-s3)

### Vanilla version with dex for auth and EBS volumes as PV
Installation steps can be found [here](vanilla)

## Add Ons - Services/Components that can be integrated with a Kubeflow deployment

### Using EFS with Kubeflow
Installation steps can be found [here](storage/efs)

### Using FSx for Lustre with Kubeflow
Installation steps can be found [here](storage/fsx-for-lustre)

## Security

The scripts in this repository are meant to be used for development/testing purposes. We highly recommend to follow AWS security best practice documentation while provisioning AWS resources. We have added few references below.

[Security best practices for Amazon Elastic Kubernetes Service (EKS)](https://aws.github.io/aws-eks-best-practices/security/docs/)  
[Security best practices for AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)  
[Security best practices for Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.Security.html)  
[Security best practices for Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)  
[Security in Amazon Route53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/security.html)  
[Security in Amazon Certificate Manager (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/security.html)  
[Security best practices for Amazon Cognito user pools](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)  
[Security in Amazon Elastic Load Balancing (ELB)](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/security.html)

## Usage Tracking

AWS uses customer feedback and usage information to improve the quality of the services and software we offer to customers. We have added usage data collection to the AWS Kubeflow distribution in order to better understand customer usage and guide future improvements. Usage tracking for Kubeflow is activated by default, but is entirely voluntary and can be deactivated at any time. 

Usage tracking for Kubeflow on AWS collects the instance ID used by one of the worker nodes in a customer’s cluster. This data is sent back to AWS once per day. Usage tracking only collects the EC2 instance ID where Kubeflow is running and does not collect or export any other data to AWS. If you wish to deactivate this tracking, instructions are below. 

### How to activate usage tracking

Usage tracking is activated by default. If you deactivated usage tracking for your Kubeflow deployment and would like to activate it after the fact, you can do so at any time with the following command:

- ```
  kustomize build distributions/aws/aws-telemetry | kubectl apply -f -
  ```

### How to deactivate usage tracking

**Before deploying Kubeflow:** 

You can deactivate usage tracking by skipping the telemetry component installation in one of two ways:

1. For single line installation, comment out the `aws-telemetry` line in the `kustomization.yaml` file. e.g. in [cognito-rds-s3 kustomization.yaml](cognito-rds-s3/kustomization.yaml#L59) file:
    ```
    # ./../aws-telemetry
    ```
1. For individual component installation, **do not** install the `aws-telemetry` component: 
    ```
    # AWS Telemetry - This is an optional component. See usage tracking documentation for more information
    kustomize build distributions/aws/aws-telemetry | kubectl apply -f -
    ```
**After deploying Kubeflow:**

To deactivate usage tracking on an existing deployment, delete the `aws-kubeflow-telemetry` cronjob with the following command:

```
kubectl delete cronjob -n kubeflow aws-kubeflow-telemetry
```

### Information collected by usage tracking

* **Instance ID** - We collect the instance ID used by one of the worker nodes in the customer’s EKS cluster. This collection occurs once per day.

### Learn more

The telemetry data we collect is in accordance with AWS data privacy policies. For more information, see the following:

* [AWS Service Terms](https://aws.amazon.com/service-terms/)
* [Data Privacy](https://aws.amazon.com/compliance/data-privacy-faq/)