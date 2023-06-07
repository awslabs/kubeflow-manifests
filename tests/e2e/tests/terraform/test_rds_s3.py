import pytest

from e2e.utils.constants import TO_ROOT, ALTERNATE_MLMDB_NAME
from e2e.utils.config import metadata
from e2e.utils.utils import rand_name
from e2e.conftest import (
    region,
    get_accesskey,
    get_secretkey,
    get_pipeline_s3_credential_option,
)

from e2e.fixtures.clients import (
    kfp_client,
    port_forward,
    session_cookie,
    host,
    login,
    password,
    client_namespace,
)

from e2e.utils.terraform_utils import terraform_installation, get_stack_output
from e2e.test_methods import rds_s3

TEST_SUITE_NAME = "rds-s3"
TF_FOLDER = TO_ROOT + "deployments/rds-s3/terraform/"


@pytest.fixture(scope="class")
def installation(region, metadata, request):
    cluster_name = rand_name(TEST_SUITE_NAME + "-")[:18]
    db_username = rand_name("user")
    db_password = rand_name("pw")
    pipeline_s3_credential_option = get_pipeline_s3_credential_option(request)

    input_variables = {
        "cluster_name": cluster_name,
        "cluster_region": region,
        "db_username": db_username,
        "db_password": db_password,
        "pipeline_s3_credential_option": pipeline_s3_credential_option,
        "mlmdb_name": ALTERNATE_MLMDB_NAME,
        "publicly_accessible": "true",
        "deletion_protection": "false",
        "secret_recovery_window_in_days": "0",
        "force_destroy_s3_bucket": "true",
    }

    if pipeline_s3_credential_option == "static":
        input_variables["minio_aws_access_key_id"] = get_accesskey(request)
        input_variables["minio_aws_secret_access_key"] = get_secretkey(request)

    return terraform_installation(
        input_variables, TF_FOLDER, TEST_SUITE_NAME, metadata, request
    )


class TestRDSS3Terraform:
    @pytest.fixture(scope="class")
    def setup(self, metadata, installation):
        rds_s3.disable_kfp_caching(
            installation["cluster_name"], installation["cluster_region"]
        )

        metadata_file = metadata.to_file()
        print(metadata.params)
        print("Created metadata file for TestRDSS3Terraform", metadata_file)

    def test_verify_kubeflow_db(self, setup, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)

        rds_s3.test_verify_kubeflow_db(db_username, db_password, rds_endpoint)

    def test_verify_mlpipeline_db(self, setup, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)

        rds_s3.test_verify_mlpipeline_db(db_username, db_password, rds_endpoint)

    def test_verify_mlmdb(self, setup, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)
        mlmdb_name = installation["mlmdb_name"]

        rds_s3.test_verify_mlmdb(db_username, db_password, rds_endpoint, mlmdb_name)

    def test_s3_bucket_is_being_used_as_metadata_store(self, setup, installation):
        region = installation["cluster_region"]
        s3_bucket_name = get_stack_output("s3_bucket_name", TF_FOLDER)

        rds_s3.test_s3_bucket_is_being_used_as_metadata_store(s3_bucket_name, region)

    def test_kfp_experiment(self, setup, kfp_client, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)

        rds_s3.test_kfp_experiment(kfp_client, db_username, db_password, rds_endpoint)

    def test_run_pipeline(self, setup, kfp_client, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)
        s3_bucket_name = get_stack_output("s3_bucket_name", TF_FOLDER)
        region = installation["cluster_region"]

        rds_s3.test_run_pipeline(
            kfp_client, s3_bucket_name, db_username, db_password, rds_endpoint, region
        )

    def test_katib_experiment(self, setup, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)
        cluster_name = installation["cluster_name"]
        region = installation["cluster_region"]

        rds_s3.test_katib_experiment(
            cluster_name, region, db_username, db_password, rds_endpoint
        )
