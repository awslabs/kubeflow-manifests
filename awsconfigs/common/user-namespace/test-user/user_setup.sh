# Your cluster name
export CLUSTER_NAME=kf
# Your cluster region
export CLUSTER_REGION=us-east-1
# The S3 Bucket that is used by Kubeflow Pipelines
export S3_BUCKET=kf-artifact-store-20240503130017739900000008
# Your AWS Acconut ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
# Name of the profile to create
export PROFILE_NAMESPACE=test-user
# user email
export PROFILE_USER=test.user@ardentmc.com
# k8s compliant user email
export SAFE_USER_PROFILE_NAME=test-user-ardentmc-com
# RBAC role for namespace
export ROLE=admin

bash create_profile_namespace_with_rolebindings.sh
bash profile_setup.sh



