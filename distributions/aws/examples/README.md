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


## Releases and Versioning

This repository was created for the development of Kubeflow on AWS as described in the [Kubeflow distributions guidelines](https://github.com/kubeflow/community/blob/master/proposals/kubeflow-distributions.md). 

#### v1.3.1

Although the distribution manifests are hosted in this repository, many of the overlays and configuration files in this repository have a dependency on the manifests published by the Kubeflow community in the [kubeflow/manifests](https://github.com/kubeflow/manifests) repository. Hence, the AWS distribution of Kubeflow for v1.3.1 was developed on a [fork](https://github.com/awslabs/kubeflow-manifests/tree/v1.3-branch) of the `v1.3-branch` of the `kubeflow/manifests` repository. This presented several challenges for ongoing maintenance as described in [Issue #76](https://github.com/awslabs/kubeflow-manifests/issues/76). 

#### v1.4+

Starting with Kubeflow v1.4, the development of the AWS distribution of Kubeflow is done on the [`main`](https://github.com/awslabs/kubeflow-manifests/tree/main) branch. The `main` branch contains only the delta from the released manifests in the `kubeflow/manifests` repository and additional components required for the AWS distribution.

### Versioning

Kubeflow on AWS releases are built on top of Kubeflow releases and therefore use the following naming convention: `{KUBEFLOW_RELEASE_VERSION}-aws-b{BUILD_NUMBER}`.

* Ex: Kubeflow v1.3.1 on AWS version 1.0.0 will have the version `v1.3.1-aws-b1.0.0`.

`KUBEFLOW_RELEASE_VERSION` refers to [Kubeflow's released version](https://github.com/kubeflow/manifests/releases) and `BUILD_NUMBER` refers to the AWS build for that Kubeflow version. `BUILD_NUMBER` uses [semantic versioning](https://semver.org/) (SemVer) to indicate whether changes included in a particular release introduce features or bug fixes and whether or not features break backwards compatibility.

### Releases

When a version of Kubeflow on AWS is released, a Git tag with the naming convention `{KUBEFLOW_RELEASE_VERSION}-aws-b{BUILD_NUMBER}` is created. These releases can be found in the Kubeflow on AWS repository [releases](https://github.com/awslabs/kubeflow-manifests/releases) section.
