"""
Global constants module
"""

DEFAULT_HOST = "http://localhost:8080/"
DEFAULT_USER_NAMESPACE = "kubeflow-user-example-com"
DEFAULT_SYSTEM_NAMESPACE = "kube-system"
DEFAULT_USERNAME = "user@example.com"
DEFAULT_PASSWORD = "12341234"
KUBEFLOW_GROUP = "kubeflow.org"
KUBEFLOW_NAMESPACE = "kubeflow"
KUBEFLOW_VERSION = "v1.7.0"
TENSORFLOW_SERVING_VERSION = "r2.11"
ALTERNATE_MLMDB_NAME = "metadata_db"

TO_ROOT = "../../"  # As of this commit, tests are run from the tests/e2e folder
CUSTOM_RESOURCE_TEMPLATES_FOLDER = (
    TO_ROOT + "tests/e2e/resources/custom-resource-templates/"
)

DISABLE_PIPELINE_CACHING_PATCH_FILE = (
    CUSTOM_RESOURCE_TEMPLATES_FOLDER + "patch-disable-pipeline-caching.yaml"
)

# Katib experiment file names
KATIB_EXPERIMENT_RANDOM_FILE = "katib-experiment-random.yaml"

# Pipeline names
PIPELINE_XG_BOOST = "[Demo] XGBoost - Iterative model training"
PIPELINE_DATA_PASSING = "[Tutorial] Data passing in python components"
PIPELINE_SAGEMAKER_TRAINING = "[Tutorial] SageMaker Training"

# Notebook images
NOTEBOOK_IMAGE_TF_CPU = "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.3-cpu-py38-ubuntu20.04-v1.8"
