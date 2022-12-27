import os
import logging
import re
import subprocess
import time
import pytest
from e2e.utils.constants import TENSORFLOW_SERVING_VERSION
from e2e.utils.s3_for_kserve.data_bucket import S3BucketForKServe
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
AUTHORIZATION_POLICY_CONFIG_FILE = "./resources/kserve/allow-predictor.yaml"

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
def associate_oidc(cluster, region):
    associate_iam_oidc_provider(cluster_name=cluster, region=region)


@pytest.fixture(scope="class")
def kserve_iam_service_account(metadata, cluster, region, request):
    metadata_key = "aws-sa"

    service_account_name = "aws-sa"

    def on_create():
        create_iam_service_account(
            service_account_name=service_account_name,
            namespace="kubeflow-example-com",
            cluster_name=cluster,
            region=region,
            iam_policy_arns=["arn:aws:iam::aws:policy/AmazonS3FullAccess"],
        )

    def on_delete():
        delete_iam_service_account(
            service_account_name=service_account_name,
            namespace="kubeflow-example-com",
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
def s3_bucket_with_training_data(metadata, cluster, region, request):
    metadata_key = "s3-bucket"
    bucket_name = "s3-" + RANDOM_PREFIX
    bucket = S3BucketForKServe(name=bucket_name)

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
def kserve_secret(metadata, cluster, region, request):
    metadata_key = "aws-secret"

    def on_create():
        secret_config = load_yaml_file(SECRET_CONFIG_FILE)
        secret_config["metadata"]["annotations"]["serving.kserve.io/s3-region"] = region
        write_yaml_file(secret_config, SECRET_CONFIG_FILE)
        kubectl_apply(SECRET_CONFIG_FILE)
        # patch secret to IRSA in profile namespace
        exec_shell(
            'kubectl patch serviceaccount aws-sa -n kubeflow-example-com -p \'{"secrets": [{"name": "aws-secret"}]}\''
        )

    def on_delete():
        cmd = f"kubectl delete secret aws-secret -n kubeflow-example-com".split()
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
def kserve_inference_service(metadata, cluster, region, request):
    metadata_key = "kserve-inference-service"

    def on_create():
        # Namespaces created by the Kubeflow profile controller have a missing authorization policy that
        # prevents the KServe predictor and transformer from working.
        # https://github.com/kserve/kserve/issues/1558
        # https://github.com/kubeflow/kubeflow/issues/5965
        # https://github.com/awslabs/kubeflow-manifests/issues/82#issuecomment-1068641378

        print("creating allow-predictor AuthorizationPolicy...")
        kubectl_apply(AUTHORIZATION_POLICY_CONFIG_FILE)

        print("creating inference service...")
        bucket_name = metadata.get("s3-bucket")

        inference_config = load_yaml_file(INFERENCE_CONFIG_FILE)
        inference_config["spec"]["predictor"]["model"][
            "storageUri"
        ] = f"s3://{bucket_name}/saved_model_half_plus_two/"
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
            cluster_name, region, namespace="kubeflow-example-com"
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
