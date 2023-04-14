import os
import logging
import re
import subprocess
import time
import pytest
from e2e.utils.constants import TENSORFLOW_SERVING_VERSION
from e2e.utils.s3_for_training.data_bucket import S3BucketWithTrainingData
from e2e.fixtures.cluster import (
    cluster,
    create_iam_service_account,
    associate_iam_oidc_provider,
    delete_iam_service_account,
)
from e2e.utils.utils import (
    rand_name,
    write_yaml_file,
    exec_shell,
    wait_for,
    load_yaml_file,
    kubectl_apply,
)
from e2e.utils.config import configure_resource_fixture, metadata
from e2e.conftest import region
from e2e.utils.load_balancer.setup_load_balancer import create_certificates
from e2e.utils.custom_resources import get_inference_service


RANDOM_PREFIX = rand_name("kserve-")
SECRET_CONFIG_FILE = "./resources/kserve/kserve-secret.yaml"
INFERENCE_CONFIG_FILE = "./resources/kserve/inference-service.yaml"
AUTHORIZATION_POLICY_CONFIG_FILE = "./utils/kserve/allow-predictor-transformer.yaml"
PROFILE_NAMESPACE = "kubeflow-user-example-com"
logger = logging.getLogger(__name__)


@pytest.fixture(scope="class")
def clone_tensorflow_serving():
    tensorflow_serving_path = "../../serving"
    if not os.path.isdir(tensorflow_serving_path):
        retcode = subprocess.call(
            f"git clone --branch {TENSORFLOW_SERVING_VERSION} https://github.com/tensorflow/serving/ ../../serving".split()
        )
        assert retcode == 0
    else:
        print("serving directory already exists, skipping clone ...")


@pytest.fixture(scope="class")
def kserve_iam_service_account(metadata, cluster, region, request):
    metadata_key = "aws-sa"

    service_account_name = "aws-sa"

    def on_create():
        create_iam_service_account(
            service_account_name=service_account_name,
            namespace=PROFILE_NAMESPACE,
            cluster_name=cluster,
            region=region,
            iam_policy_arns=["arn:aws:iam::aws:policy/AmazonS3FullAccess"],
        )

    def on_delete():
        delete_iam_service_account(
            service_account_name=service_account_name,
            namespace=PROFILE_NAMESPACE,
            cluster_name=cluster,
            region=region,
        )

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details="created",
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


@pytest.fixture(scope="class")
def s3_bucket_with_data_kserve(metadata, kserve_secret, request):
    metadata_key = "s3-bucket-kserve"
    bucket_name = "s3-" + RANDOM_PREFIX
    bucket = S3BucketWithTrainingData(
        name=bucket_name,
        time_to_sleep=60,
        cmd=f"aws s3 sync ../../serving/tensorflow_serving/servables/tensorflow/testdata/saved_model_half_plus_two_cpu s3://{bucket_name}/saved_model_half_plus_two",
    )

    def on_create():
        bucket.create()

    def on_delete():
        bucket.delete()

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=bucket_name,
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


@pytest.fixture(scope="class")
def kserve_secret(metadata, region, kserve_iam_service_account, request):
    metadata_key = "kserve-aws-secret"

    def on_create():
        secret_config = load_yaml_file(SECRET_CONFIG_FILE)
        secret_config["metadata"]["annotations"]["serving.kserve.io/s3-region"] = region
        secret_config["metadata"]["namespace"] = PROFILE_NAMESPACE
        write_yaml_file(secret_config, SECRET_CONFIG_FILE)
        kubectl_apply(SECRET_CONFIG_FILE)
        # patch secret to IRSA in profile namespace
        cmd = f'kubectl patch serviceaccount aws-sa -n {PROFILE_NAMESPACE} -p \'{{"secrets": [{{"name": "kserve-aws-secret"}}]}}\''
        print(cmd)
        exec_shell(cmd)

    def on_delete():
        cmd = f"kubectl delete secret kserve-aws-secret -n {PROFILE_NAMESPACE}".split()
        subprocess.call(cmd)

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details="created",
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


@pytest.fixture(scope="class")
def kserve_inference_service(
    metadata,
    kserve_iam_service_account,
    s3_bucket_with_data_kserve,
    kserve_secret,
    cluster,
    region,
    request,
):
    metadata_key = "kserve-inference-service"

    def on_create():
        # Namespaces created by the Kubeflow profile controller have a missing authorization policy that
        # prevents the KServe predictor and transformer from working.
        # https://github.com/kserve/kserve/issues/1558
        # https://github.com/kubeflow/kubeflow/issues/5965
        # https://github.com/awslabs/kubeflow-manifests/issues/82#issuecomment-1068641378

        print("creating allow-predictor-transformer AuthorizationPolicy...")
        kubectl_apply(AUTHORIZATION_POLICY_CONFIG_FILE)
        print("creating inference service...")
        bucket_name = metadata.get("s3-bucket-kserve")

        inference_config = load_yaml_file(INFERENCE_CONFIG_FILE)
        inference_config["spec"]["predictor"]["model"][
            "storageUri"
        ] = f"s3://{bucket_name}/saved_model_half_plus_two/"
        inference_config["metadata"]["namespace"] = PROFILE_NAMESPACE
        write_yaml_file(inference_config, INFERENCE_CONFIG_FILE)
        kubectl_apply(INFERENCE_CONFIG_FILE)
        wait_for_inference(cluster, region)

    def on_delete():
        cmd = f"kubectl delete -f {INFERENCE_CONFIG_FILE}".split()
        subprocess.call(cmd)

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details="created",
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


def wait_for_inference(cluster_name: str, region: str):
    logger.info("waiting for inference service creation ...")

    def callback():
        inference_service = get_inference_service(
            cluster_name, region, namespace=PROFILE_NAMESPACE
        )

        assert inference_service.get("status") is not None
        conditions = inference_service["status"]["conditions"]
        for condition in conditions:
            if condition["type"] == "IngressReady":
                assert condition["status"] == "True"
            if condition["type"] == "PredictorConfigurationReady":
                assert condition["status"] == "True"
            if condition["type"] == "PredictorRouteReady":
                assert condition["status"] == "True"
            if condition["type"] == "PredictorReady":
                assert condition["status"] == "True"

    wait_for(callback)
