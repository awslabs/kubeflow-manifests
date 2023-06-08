import pytest

from e2e.utils.constants import TO_ROOT
from e2e.utils.config import metadata
from e2e.utils.utils import rand_name
from e2e.conftest import region, get_root_domain_name

from e2e.utils.terraform_utils import terraform_installation
from e2e.test_methods import cognito

TEST_SUITE_NAME = "tf-cognito"
TF_FOLDER = TO_ROOT + "deployments/cognito/terraform/"


@pytest.fixture(scope="class")
def installation(region, metadata, request):
    cluster_name = rand_name(TEST_SUITE_NAME + "-")[:18]
    subdomain_name = rand_name("sub") + "." + get_root_domain_name(request)
    cognito_user_pool_name = rand_name("up-")

    input_variables = {
        "cluster_name": cluster_name,
        "cluster_region": region,
        "aws_route53_root_zone_name": get_root_domain_name(request),
        "aws_route53_subdomain_zone_name": subdomain_name,
        "cognito_user_pool_name": cognito_user_pool_name,
    }

    return terraform_installation(
        input_variables, TF_FOLDER, TEST_SUITE_NAME, metadata, request
    )


class TestCognitoTerraform:
    @pytest.fixture(scope="class")
    def setup(self, metadata, installation):
        metadata_file = metadata.to_file()
        print(metadata.params)
        print("Created metadata file for TestCognitoTerraform", metadata_file)

    def test_url_is_up(self, setup, installation):
        subdomain_name = installation["aws_route53_subdomain_zone_name"]

        cognito.test_url_is_up(subdomain_name)
