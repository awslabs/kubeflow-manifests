# AWS Distribution of Kubeflow

## Deployment Options

In this directory you can find instructions for deploying Kubeflow on Amazon Elastic Kubernetes Service (Amazon EKS). Depending upon your use case you may choose to integrate your deployment with different AWS services. Following are various deployment options:

### Components configured for RDS and S3
Installation steps can be found [here](rds-s3)

### Components configured for Cognito
Installation steps can be found [here](cognito)

### Components configured for Cognito, RDS and S3
Installation steps can be found [here](cognito-rds-s3)

### Vanilla version with dex for auth and ebs volumes as PV
Installation steps can be found [here](vanilla)

## Add Ons - Services/Components that can be integrated with a Kubeflow deployment

### Using EFS with Kubeflow
Installation steps can be found [here](add-ons/storage/efs)

### Using FSx for Lustre with Kubeflow
Installation steps can be found [here](add-ons/storage/fsx-for-lustre)

## Security

We highly recommend to follow AWS security best practice documentation while provisioning AWS resources. We have added few references below.

[Security best practices for Amazon Elastic Kubernetes Service (EKS)](https://aws.github.io/aws-eks-best-practices/security/docs/)  
[Security best practices for AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)  
[Security best practices for Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.Security.html)  
[Security best practices for Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)  
[Security in Amazon Route53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/security.html)  
[Security in Amazon Certificate Manager (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/security.html)  
[Security best practices for Amazon Cognito user pools](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)  
[Security in Amazon Elastic Load Balancing (ELB)](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/security.html)