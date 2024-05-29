# PREREQUISITE: create a username on AWS Cognito's kfuserpool with the same username as 
# is present in ardent email
# example: test.user@ardentmc.com
# AWS Cognito user: test.user
# Your cluster name
export CLUSTER_NAME=kf
# Your cluster region
export CLUSTER_REGION=us-east-1
# The S3 Bucket that is used by Kubeflow Pipelines
export S3_BUCKET=kf-artifact-store-20240503130017739900000008
# Your AWS Acconut ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
# Name of the profile to create, no "."'s
export PROFILE_NAMESPACE=justin-howard
# Ardent email
export PROFILE_USER=justin.howard@ardentmc.com

aws --region $CLUSTER_REGION eks update-kubeconfig --name $CLUSTER_NAME

export OIDC_URL=$(aws eks describe-cluster --region $CLUSTER_REGION --name $CLUSTER_NAME  --query "cluster.identity.oidc.issuer" --output text | cut -c9-)


cat <<EOF > trust.json
{
"Version": "2012-10-17",
"Statement": [
    {
    "Effect": "Allow",
    "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/${OIDC_URL}"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
        "StringEquals": {
        "${OIDC_URL}:aud": "sts.amazonaws.com",
        "${OIDC_URL}:sub": "system:serviceaccount:${PROFILE_NAMESPACE}:default-editor"
        }
    }
    }
]
}
EOF

cat <<EOF > s3_policy.json
{
    "Version": "2012-10-17",
    "Statement": [
           {
        "Effect": "Allow",
        "Action": "s3:*",
        "Resource": [
            "arn:aws:s3:::${S3_BUCKET}",
            "arn:aws:s3:::${S3_BUCKET}/*"
              ]
           }
     ]
}
EOF

aws iam create-role --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --assume-role-policy-document file://trust.json

aws --region $CLUSTER_REGION iam put-role-policy --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --policy-name kf-$PROFILE_NAMESPACE-pipeline-s3 --policy-document file://s3_policy.json  



cat <<EOF > profile_iam.yaml
apiVersion: kubeflow.org/v1
kind: Profile
metadata:
  name: ${PROFILE_NAMESPACE}
  namespace: kubeflow
spec:
  owner:
    kind: User
    name: ${PROFILE_USER}
  plugins:
  - kind: AwsIamForServiceAccount
    spec:
      awsIamRole: $(aws iam get-role --role-name $PROFILE_NAMESPACE-$CLUSTER_NAME-role --output text --query 'Role.Arn')
      annotateOnly: true
EOF

# to create a new user
kubectl create -f profile_iam.yaml
# to edit an existing user
# kubectl apply -f profile_iam.yaml



