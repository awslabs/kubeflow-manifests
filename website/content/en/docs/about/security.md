+++
title = "Security"
description = "Follow AWS security best practices when using Kubeflow on AWS"
weight = 40
+++

We highly recommend that you follow AWS security best practices while provisioning any AWS resources. 

## Default security configuration

### Amazon Simple Storage Service (S3)

#### Block public access

The Amazon S3 bucket created for Kubeflow artifacts has a default ["block public access" configuration](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html). 

#### Encryption

When you use Amazon S3 for kubeflow artifact storage, Kubeflow on AWS configures the Amazon S3 bucket to use [server-side encryption with Amazon S3-managed encryption keys](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingServerSideEncryption.html) (SSE-S3). If you prefer to use [server-side encryption with AWS Key Management Service](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingKMSEncryption.html) (SSE-KMS), you can modify these files to specify an AWS KMS key.

* [main.tf](https://github.com/awslabs/kubeflow-manifests/blob/main/iaac/terraform/aws-infra/s3/main.tf) for Terraform deployments
* [auto-rds-s3-setup.py](https://github.com/awslabs/kubeflow-manifests/blob/main/tests/e2e/utils/rds-s3/auto-rds-s3-setup.py) for manifest deployments

Both SSE-S3 and SSE-KMS provide encryption of objects in the Amazon S3 bucket. You may prefer SSE-KMS if you want to separate the management of encryption keys (via AWS KMS) from management of the Amazon S3 bucket. That separation may provide a stronger security posture. In order to access and use an object in an Amazon S3 bucket, a user needs permission to read the object in the Amazon S3 bucket as well as permission to use the AWS KMS encryption key.

## Security resources

Refer to the following documents for more information: 

* [Security best practices for Amazon Elastic Kubernetes Service (EKS)](https://aws.github.io/aws-eks-best-practices/security/docs/)  
* [Security best practices for AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)  
* [Security best practices for Amazon Relational Database Service (RDS)](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.Security.html)  
* [Security best practices for Amazon Simple Storage Service (S3)](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)  
* [Security in Amazon Route53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/security.html)  
* [Security in Amazon Certificate Manager (ACM)](https://docs.aws.amazon.com/acm/latest/userguide/security.html)  
* [Security best practices for Amazon Cognito user pools](https://docs.aws.amazon.com/cognito/latest/developerguide/managing-security.html)  
* [Security in Amazon Elastic Load Balancing (ELB)](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/security.html)
