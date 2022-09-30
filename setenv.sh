#!/bin/sh

export CLUSTER_REGION=us-west-1
export CLUSTER_NAME=mlp-eks
export KUBECONFIG=~/.kube/eksctl.cfg
export S3_BUCKET=mlp-mlops-kubeflow
export DB_INSTANCE_NAME=mlp-mlops-mysql
export AWS_ACCESS_KEY_ID=AKIAQMTCWG66V43QMVGQ
export AWS_SECRET_ACCESS_KEY=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
export MINIO_AWS_ACCESS_KEY_ID=AKIAQMTCWG66V43QMVGQ
export MINIO_AWS_SECRET_ACCESS_KEY=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
export RDS_SECRET_NAME=mlp-mlops-rds-secret-1
export S3_SECRET_NAME=mlp-mlops-s3-secret-1
