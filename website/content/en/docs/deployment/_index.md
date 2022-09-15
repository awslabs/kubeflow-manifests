+++
title = "Deployment Options"
description = "Deploy Kubeflow on AWS"
weight = 20
+++
Kubeflow on AWS provides its own Kubeflow manifests that support integrations with various AWS services that are highly available and scalable. This reduces the operational overhead of maintaining the Kubeflow platform. 

If you want to deploy Kubeflow with minimal changes, but optimized for [Amazon Elastic Kubernetes Service](https://aws.amazon.com/eks/) (Amazon EKS), then consider the [vanilla]({{< ref "/docs/deployment/vanilla/guide.md" >}}) deployment option. The Kubeflow control plane is installed on top of Amazon EKS, which is a managed container service used to run and scale Kubernetes applications in the cloud.

To take greater advantage of the distribution and make use of the AWS managed services, choose one of the following deployment options according to your organization's requirements:
- Kubeflow on AWS provides integration with the [Amazon Relational Database Service](https://aws.amazon.com/rds/) (RDS) for highly scalable and available pipelines and metadata store. RDS removes the need to manage a local MYSQL database service and storage. For more information, see the [RDS deployment guide]({{< ref "/docs/deployment/rds-s3/guide.md#using-only-rds-or-only-s3" >}}). 
- Integrate your deployment with [Amazon Simple Storage Service](https://aws.amazon.com/s3/) (S3) for an easy-to-use pipeline artifacts store. S3 removes the need to host the local object storage MinIO. For more information, see the [S3 deployment guide]({{< ref "/docs/deployment/rds-s3/guide.md#using-only-rds-or-only-s3" >}}). 
- You can also deploy Kubeflow on AWS with both RDS and S3 integrations using the [RDS and S3 deployment guide]({{< ref "/docs/deployment/rds-s3/guide.md" >}}).
- Use [AWS Cognito](https://aws.amazon.com/cognito/) for Kubeflow user authentication, which removes the complexity of managing users or [Dex connectors](https://dexidp.io/docs/connectors/) in Kubeflow’s native Dex authentication service. For more information, see the [Cognito deployment guides]({{< ref "/docs/deployment/cognito" >}}). 
- You can also deploy Kubeflow on AWS with all three service integrations by following the [Cognito, RDS, and S3 deployment guide]({{< ref "/docs/deployment/cognito-rds-s3/guide.md" >}}). 

