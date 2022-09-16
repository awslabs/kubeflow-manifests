"""
Installs the vanilla distribution of kubeflow and validates the installation by:
    - Creating, describing, and deleting a KFP experiment
    - Running a pipeline that comes with the default kubeflow installation
    - Creating, describing, and deleting a Katib experiment
"""

import os
import subprocess
import json
import time
import pytest

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import load_yaml_file, wait_for, rand_name, write_yaml_file
from e2e.utils.config import configure_resource_fixture, metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, clone_upstream #, configure_manifests
from e2e.fixtures.clients import (
    kfp_client,
    port_forward,
    session_cookie,
    host,
    login,
    password,
    client_namespace,
    account_id
)
from e2e.fixtures.profile_dependencies import (
    configure_manifests,
    profile_controller_policy,
    profile_controller_service_account,
    profile_trust_policy,
    profile_role,
    associate_oidc,
    kustomize_path,
    client_namespace,
    login,
)

from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from e2e.utils.load_balancer.common import CONFIG_FILE as LB_CONFIG_FILE
from kfp_server_api.exceptions import ApiException as KFPApiException
from kubernetes.client.exceptions import ApiException as K8sApiException
from e2e.utils.aws.iam import IAMRole
from e2e.utils.s3_for_training.data_bucket import S3BucketWithTrainingData


GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../deployments/vanilla"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH


PIPELINE_NAME = "[Tutorial] Data passing in python components"
PIPELINE_NAME_KFP = "[Tutorial] SageMaker Training"
KATIB_EXPERIMENT_FILE = "katib-experiment-random.yaml"


def wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id):
    def callback():
        resp = kfp_client.get_run(run.id).run

        assert resp.name == job_name
        assert resp.pipeline_spec.pipeline_id == pipeline_id
        assert resp.status == "Succeeded"

    wait_for(callback, 600)

def create_execution_role(
    role_name, region,
):

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    managed_policies = ["AmazonS3FullAccess", "AmazonSageMakerFullAccess"]

    role = IAMRole(name=role_name, region=region, policies=managed_policies)
    return role.create(
        policy_document=json.dumps(trust_policy)
    )


def create_s3_bucket_with_data(
    bucket_name, region,
):

    bucket = S3BucketWithTrainingData(name=bucket_name, region=region)
    bucket.create()


class TestSanity:
    @pytest.fixture(scope="class")
    def setup(self):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestSanity", metadata_file)

    def test_kfp_experiment(self, kfp_client):
        name = rand_name("experiment-")
        description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            name, description=description, namespace=DEFAULT_USER_NAMESPACE
        )

        assert name == experiment.name
        assert description == experiment.description
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id

        resp = kfp_client.get_experiment(
            experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
        )

        assert name == resp.name
        assert description == resp.description
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id

        kfp_client.delete_experiment(experiment.id)

        try:
            kfp_client.get_experiment(
                experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
            )
            raise AssertionError("Expected KFPApiException Not Found")
        except KFPApiException as e:
            assert "Not Found" == e.reason

    def test_run_pipeline(self, kfp_client):
        experiment_name = rand_name("experiment-")
        experiment_description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            experiment_name,
            description=experiment_description,
            namespace=DEFAULT_USER_NAMESPACE,
        )

        pipeline_id = kfp_client.get_pipeline_id(PIPELINE_NAME)
        job_name = rand_name("run-")

        run = kfp_client.run_pipeline(
            experiment.id, job_name=job_name, pipeline_id=pipeline_id
        )

        assert run.name == job_name
        assert run.pipeline_spec.pipeline_id == pipeline_id
        assert run.status == None

        wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

        kfp_client.delete_experiment(experiment.id)

    def test_katib_experiment(self, cluster, region):
        filepath = os.path.abspath(
            os.path.join(CUSTOM_RESOURCE_TEMPLATES_FOLDER, KATIB_EXPERIMENT_FILE)
        )

        name = rand_name("katib-random-")
        namespace = DEFAULT_USER_NAMESPACE
        replacements = {"NAME": name, "NAMESPACE": namespace}

        resp = create_katib_experiment_from_yaml(
            cluster, region, filepath, namespace, replacements
        )

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        resp = get_katib_experiment(cluster, region, namespace, name)

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        resp = delete_katib_experiment(cluster, region, namespace, name)

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        try:
            get_katib_experiment(cluster, region, namespace, name)
            raise AssertionError("Expected K8sApiException Not Found")
        except K8sApiException as e:
            assert "Not Found" == e.reason

    def test_run_kfp_sagemaker_pipeline(
        self, region, metadata, kfp_client,
    ):

        random_prefix = rand_name("kfp-")
        experiment_name = "experiment-" + random_prefix
        experiment_description = "description-" + random_prefix
        sagemaker_execution_role_name = "role-" + random_prefix
        bucket_name = "s3-" + random_prefix
        job_name = "kfp-run-" + random_prefix

        sagemaker_execution_role_arn = create_execution_role(
            sagemaker_execution_role_name, region
        )
        create_s3_bucket_with_data(bucket_name, "us-east-1")
        time.sleep(120)

        experiment = kfp_client.create_experiment(
            experiment_name,
            description=experiment_description,
            namespace=DEFAULT_USER_NAMESPACE,
        )

        pipeline_id = kfp_client.get_pipeline_id(PIPELINE_NAME_KFP)

        params = {
            "sagemaker_role_arn": sagemaker_execution_role_arn,
            "s3_bucket_name": bucket_name,
        }

        run = kfp_client.run_pipeline(
            experiment.id, job_name=job_name, pipeline_id=pipeline_id, params=params
        )

        assert run.name == job_name
        assert run.pipeline_spec.pipeline_id == pipeline_id
        assert run.status == None

        wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

        kfp_client.delete_experiment(experiment.id)