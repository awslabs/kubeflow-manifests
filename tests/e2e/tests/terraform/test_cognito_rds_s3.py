import pytest

from e2e.utils.constants import TO_ROOT, ALTERNATE_MLMDB_NAME
from e2e.utils.config import metadata
from e2e.utils.utils import rand_name
from e2e.conftest import (
    region,
    get_accesskey,
    get_secretkey,
    get_root_domain_name,
    get_pipeline_s3_credential_option,
)

from e2e.utils.terraform_utils import terraform_installation, get_stack_output
from e2e.test_methods import cognito, rds_s3

TEST_SUITE_NAME = "cog-rds-s3"
TF_FOLDER = TO_ROOT + "deployments/cognito-rds-s3/terraform/"


@pytest.fixture(scope="class")
def installation(region, metadata, request):
    cluster_name = rand_name(TEST_SUITE_NAME + "-")[:18]
    db_username = rand_name("user")
    db_password = rand_name("pw")
    subdomain_name = rand_name("sub") + "." + get_root_domain_name(request)
    cognito_user_pool_name = rand_name("up-")
    pipeline_s3_credential_option = get_pipeline_s3_credential_option(request)

    input_variables = {
        "cluster_name": cluster_name,
        "cluster_region": region,
        "db_username": db_username,
        "db_password": db_password,
        "mlmdb_name": ALTERNATE_MLMDB_NAME,
        "publicly_accessible": "true",
        "deletion_protection": "false",
        "secret_recovery_window_in_days": "0",
        "force_destroy_s3_bucket": "true",
        "aws_route53_root_zone_name": get_root_domain_name(request),
        "aws_route53_subdomain_zone_name": subdomain_name,
        "cognito_user_pool_name": cognito_user_pool_name,
        "pipeline_s3_credential_option": pipeline_s3_credential_option,
    }

    if pipeline_s3_credential_option == "static":
        input_variables["minio_aws_access_key_id"] = get_accesskey(request)
        input_variables["minio_aws_secret_access_key"] = get_secretkey(request)

    return terraform_installation(
        input_variables, TF_FOLDER, TEST_SUITE_NAME, metadata, request
    )


class TestCognitoRDSS3Terraform:
    @pytest.fixture(scope="class")
    def setup(self, metadata, installation):
        rds_s3.disable_kfp_caching(
            installation["cluster_name"], installation["cluster_region"]
        )

        metadata_file = metadata.to_file()
        print(metadata.params)
        print("Created metadata file for TestCognitoRDSS3Terraform", metadata_file)

    def test_url_is_up(self, setup, installation):
        subdomain_name = installation["aws_route53_subdomain_zone_name"]

        cognito.test_url_is_up(subdomain_name)

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

    def test_katib_experiment(self, setup, installation):
        db_username = installation["db_username"]
        db_password = installation["db_password"]
        rds_endpoint = get_stack_output("rds_endpoint", TF_FOLDER)
        cluster_name = installation["cluster_name"]
        region = installation["cluster_region"]

        rds_s3.test_katib_experiment(
            cluster_name, region, db_username, db_password, rds_endpoint
        )
