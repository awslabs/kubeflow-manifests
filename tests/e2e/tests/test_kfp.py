import subprocess
import pytest
import json, time

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata, configure_resource_fixture, configure_env_file

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, clone_upstream
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
from e2e.fixtures.clients import (
    account_id,
    kfp_client,
    port_forward,
    session_cookie,
    host,
    password,
)
from e2e.utils.aws.iam import IAMRole
from e2e.utils.s3_for_training.data_bucket import S3BucketWithTrainingData
from e2e.utils.utils import load_yaml_file, wait_for, rand_name, write_yaml_file


CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"
PIPELINE_NAME = "[Tutorial] SageMaker Training"


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


class TestKFPPipeline:
    @pytest.fixture(scope="function")
    def setup(self, metadata, configure_manifests, kustomize):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for KFP Pipeline Test", metadata_file)

    def test_run_pipeline(
        self, setup, region, metadata, kfp_client, configure_manifests,
    ):

        random_prefix = rand_name("kfp-")
        profile_role = configure_manifests["profile_role"]
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

        pipeline_id = kfp_client.get_pipeline_id(PIPELINE_NAME)

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
