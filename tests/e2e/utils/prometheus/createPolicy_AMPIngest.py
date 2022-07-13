from e2e.utils.prometheus.IAMPolicyUtils import *
from e2e.utils.utils import get_aws_account_id
from e2e.fixtures.cluster import get_oidc_provider

# Global Variables
PROMETHEUS_NAMESPACE = "monitoring"
SERVICE_ACCOUNT_AMP_INGEST_NAME = "amp-iamproxy-ingest-service-account"
SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE = "amp-iamproxy-ingest-role"
SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY = "AMPIngestPolicy"
PERMISSION_POLICY_FILE_PATH = "../../deployments/add-ons/prometheus/AMPIngestPermissionPolicy"

def create_AMP_ingest_policy():
    return create_policy_if_not_exist(SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY, PERMISSION_POLICY_FILE_PATH)

def delete_policy():
    delete_IAM_policy(SERVICE_ACCOUNT_IAM_AMP_INGEST_POLICY)
