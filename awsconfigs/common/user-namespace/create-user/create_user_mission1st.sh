# Your cluster name
export CLUSTER_NAME=kf
# Your cluster region
export CLUSTER_REGION=us-east-1
# The S3 Bucket that is used by Kubeflow Pipelines
export S3_BUCKET=kf-artifact-store-20240503130017739900000008
# Your AWS Acconut ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
# user first name
export FIRSTNAME=d
# user last name
export LASTNAME=tejada
# organization
export ORGANIZATION=mission1st
# ending
export END=pr
# Name of the profile to create
export PROFILE_NAMESPACE=${FIRSTNAME}${LASTNAME}
# user email
export PROFILE_USER=${FIRSTNAME}${LASTNAME}@${ORGANIZATION}.${END}
# k8s compliant user email
export SAFE_USER_PROFILE_NAME=${FIRSTNAME}${LASTNAME}-${ORGANIZATION}-${END}
# RBAC role for namespace
export ROLE=admin

bash ../profile_namespace_creation/create_profile_namespace_with_rolebindings.sh
bash ../profile_namespace_creation/profile_setup.sh

# clean up created files. If debugging, uncomment these.
rm *yaml
rm *json

