"""
Global constants module
"""

# Generic

DEFAULT_HOST = "http://localhost:8080/"
DEFAULT_USER_NAMESPACE = "kubeflow-user-example-com"
DEFAULT_USERNAME = "user@example.com"
DEFAULT_PASSWORD = "12341234"
KUBEFLOW_GROUP = "kubeflow.org"
KUBEFLOW_NAMESPACE = "kubeflow"
KUBEFLOW_SERVICE_ACCOUNT_NAME = "kubeflow-secrets-manager-sa"

# IAM

IAM_AWS_SSM_READ_ONLY_POLICY = "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess"
IAM_SECRETS_MANAGER_READ_WRITE_POLICY = (
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
)
