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