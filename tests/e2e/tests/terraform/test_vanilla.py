import pytest

from e2e.utils.constants import TO_ROOT
from e2e.utils.config import metadata
from e2e.utils.utils import rand_name
from e2e.conftest import region

from e2e.fixtures.clients import (
    kfp_client,
    port_forward,
    session_cookie,
    host,
    login,
    password,
    client_namespace,
)

from e2e.fixtures.notebook_dependencies import notebook_server

from e2e.utils.terraform_utils import terraform_installation
from e2e.test_methods import vanilla
from e2e.test_methods.vanilla import sagemaker_execution_role, s3_bucket_with_data, clean_up_training_jobs_in_user_ns

TEST_SUITE_NAME = "tf-vanilla"
TF_FOLDER = TO_ROOT + "deployments/vanilla/terraform/"


@pytest.fixture(scope="class")
def installation(region, metadata, request):
    cluster_name = rand_name(TEST_SUITE_NAME + "-")[:18]

    input_variables = {
        "cluster_name": cluster_name,
        "cluster_region": region,
    }

    return terraform_installation(
        input_variables, TF_FOLDER, TEST_SUITE_NAME, metadata, request
    )


class TestVanillaTerraform:
    @pytest.fixture(scope="class")
    def setup(self, metadata, installation):
        metadata_file = metadata.to_file()
        print(metadata.params)
        print("Created metadata file for TestVanillaTerraform", metadata_file)

    def test_kfp_experiment(self, setup, kfp_client):
        vanilla.test_kfp_experiment(kfp_client)

    def test_run_pipeline(self, setup, kfp_client):
        vanilla.test_run_pipeline(kfp_client)

    def test_katib_experiment(self, setup, installation):
        cluster = installation["cluster_name"]
        region = installation["cluster_region"]

        vanilla.test_katib_experiment(cluster, region)

    @pytest.mark.parametrize(
        "framework_name, image_name, ipynb_notebook_file, expected_output",
        vanilla.TEST_ACK_CRDS_PARAMS,
    )
    def test_ack_crds(
        self,
        setup,
        region,
        metadata,
        notebook_server,
        framework_name,
        image_name,
        ipynb_notebook_file,
        expected_output,
    ):
        vanilla.test_ack_crds(
            notebook_server, framework_name, ipynb_notebook_file, expected_output
        )

    @pytest.mark.parametrize(
        "user_namespace", 
        vanilla.TEST_KFP_SM_PARAMS,
    )
    def test_run_kfp_sagemaker_pipeline(
        self, setup, kfp_client, sagemaker_execution_role, s3_bucket_with_data, clean_up_training_jobs_in_user_ns, user_namespace
    ):
        vanilla.test_run_kfp_sagemaker_pipeline(
            kfp_client, s3_bucket_with_data.name, sagemaker_execution_role.arn, clean_up_training_jobs_in_user_ns, user_namespace
        )
