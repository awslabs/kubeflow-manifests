from e2e.utils.prometheus.IAMRolesUtils import *

# Global Variables
SERVICE_ACCOUNT_NAMESPACE = "monitoring"
SERVICE_ACCOUNT_AMP_INGEST_NAME = "amp-iamproxy-ingest-service-account"
SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE = "amp-iamproxy-ingest-role"
SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY = "AMPIngestPolicy"
TRUST_POLICY_FILE_NAME = "AMPTrustPolicy"
PERMISSION_POLICY_FILE_NAME = "AMPIngestPermissionPolicy"

# Create a trust policy json file
def create_AMP_trust_policy_file():
    aws_account_id = get_AWS_account_ID()
    oidc_provider = get_OIDC_provider(CLUSTER_NAME, CLUSTER_REGION)
    trust_policy = open(TRUST_POLICY_FILE_NAME + '.json', 'w')
    trust_policy.write('\n'.join([
        '{',
        '  "Version": "2012-10-17",',
        '  "Statement": [',
        '    {',
        '      "Effect": "Allow",',
        '      "Principal": {',
        f'        "Federated": "arn:aws:iam::{aws_account_id}:oidc-provider/{oidc_provider}"',
        '      },',
        '      "Action": "sts:AssumeRoleWithWebIdentity",',
        '      "Condition": {',
        '        "StringEquals": {',
        f'          "{oidc_provider}:sub": "system:serviceaccount:{SERVICE_ACCOUNT_NAMESPACE}:{SERVICE_ACCOUNT_AMP_INGEST_NAME}"',
        '        }',
        '      }',
        '    }',
        '  ]',
        '}']))
    trust_policy.close()

# Create a permission policy json file
def create_AMP_permission_policy_file():
    permission_policy = open(PERMISSION_POLICY_FILE_NAME + '.json', 'w')
    permission_policy.write('\n'.join([
        '{',
        '  "Version": "2012-10-17",',
        '   "Statement": [',
        '       {"Effect": "Allow",',
        '        "Action": [',
        '           "aps:RemoteWrite", ',
        '           "aps:GetSeries", ',
        '           "aps:GetLabels",',
        '           "aps:GetMetricMetadata"',
        '        ], ',
        '        "Resource": "*"',
        '      }',
        '   ]',
        '}']))
    permission_policy.close()

def setup_ingest_role(cluster_name, cluster_region):
    global CLUSTER_NAME, CLUSTER_REGION
    CLUSTER_NAME = cluster_name
    CLUSTER_REGION = cluster_region
    
    setup_role_and_policy(
        SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE, SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY,
        TRUST_POLICY_FILE_NAME, PERMISSION_POLICY_FILE_NAME,
        create_AMP_trust_policy_file, create_AMP_permission_policy_file)
    
    associate_OIDC_with_IAM(CLUSTER_NAME, CLUSTER_REGION)

def delete_ingest_role():
    print("Deleting policy function called.")
    delete_IAM_policy(SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE, SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY)
    print("Deleting role function called.")
    delete_IAM_role(SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE)
