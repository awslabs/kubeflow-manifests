# AWS AuthService

## Overview
AWS AuthService is an HTTP Server that handles the logging out of an Authenticated user who was connected to Kubeflow using AWS Cognito and Amazon ALB.

## Design
An HTTP Server that listens for a users logout request that then follows the two steps necessary to logout an Authenticated Cognito + ALB user. These being expiring any ALB Cookies and then hitting the Cognito Logout Endpoint. Official [Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#authentication-logout) lists these steps as required for secure logout.

## Manifests
To install AWS AuthService apply them to your EKS Cluster. The manifests can be found in [awsconfigs](../../awsconfigs/common/aws-authservice/base/).

```
kubectl apply -k ../../awsconfigs/common/aws-authservice/base/
```

## Options
These are configurable environment variables used by AWS AuthService in [params.env](../../awsconfigs/common/aws-authservice/base/params.env)

`LOGOUT_URL`: The Cognito URL that will be redirected to on Logout.

`PORT`: The Port that AWS AuthService runs the HTTP server on. (Default Value of 8082). Additionally have to configure the port in the respective yaml files in [aws-authservice/base](../../awsconfigs/common/aws-authservice/base/)

## Build
The image can be built using Docker.
- Docker: make build

## References
[Logout Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html#authentication-logout)

Inspired by [oidc-authservice](https://github.com/arrikto/oidc-authservice)


## Licensing
See the [LICENSE](../../LICENSE) file for our project's licensing. 

