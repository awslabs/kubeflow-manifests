"""
Add additional pytest supported test configurations.

https://docs.pytest.org/en/6.2.x/example/simple.html
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--metadata", action="store", help="Metadata file to resume a test class from."
    )
    parser.addoption(
        "--keepsuccess",
        action="store_true",
        default=False,
        help="Keep successfully created resources on delete.",
    )
    parser.addoption(
        "--deletecluster",
        action="store_true",
        default=False,
        help="Delete EKS cluster",
    )
    parser.addoption(
        "--region",
        action="store",
        help="Region to run the tests in. Will be overriden if metadata is provided and region is present.",
    )
    parser.addoption(
        "--root-domain-name",
        action="store",
        help="Root domain name for which subdomain will be created. Required for tests which use cognito",
    )
    parser.addoption(
        "--root-domain-hosted-zone-id",
        action="store",
        help="Hosted zone id of the root domain. Required for tests which use cognito",
    )
    parser.addoption(
        "--accesskey",
        action="store",
        help="AWS account accesskey",
    )
    parser.addoption(
        "--secretkey",
        action="store",
        help="AWS account secretkey",
    )
    parser.addoption(
        "--installation_option",
        action="store",
        help="helm or kustomize, default is set to kustomize",
    )
    parser.addoption(
        "--deployment_option",
        action="store",
        help="vanilla/cognito/rds-and-s3/rds-only/s3-only, default is set to vanilla",
    )
    parser.addoption(
        "--pipeline_s3_credential_option",
        action="store",
        help="irsa or static, default is set to static",
    )


def keep_successfully_created_resource(request):
    return request.config.getoption("--keepsuccess")


def clean_up_eks_cluster(request):
    return request.config.getoption("--deletecluster")


def load_metadata_file(request):
    return request.config.getoption("--metadata")


def get_accesskey(request):
    access_key = request.config.getoption("--accesskey")
    if not access_key:
        pytest.fail("--accesskey is required")
    return access_key


def get_secretkey(request):
    secret_key = request.config.getoption("--secretkey")
    if not secret_key:
        pytest.fail("--secretkey is required")
    return secret_key


def get_installation_option(request):
    installation_option = request.config.getoption("--installation_option")
    if not installation_option:
        installation_option = "kustomize"
    return installation_option


def get_deployment_option(request):
    deployment_option = request.config.getoption("--deployment_option")
    if not deployment_option:
        deployment_option = "vanilla"
    return deployment_option


def get_root_domain_name(request):
    return request.config.getoption("--root-domain-name")


def get_pipeline_s3_credential_option(request):
    pipeline_s3_credential_option = request.config.getoption(
        "--pipeline_s3_credential_option"
    )
    if not pipeline_s3_credential_option:
        pipeline_s3_credential_option = "static"
    return pipeline_s3_credential_option

@pytest.fixture(scope="class")
def region(metadata, request):
    """
    Test region.
    """

    if metadata.get("region"):
        return metadata.get("region")

    region = request.config.getoption("--region")
    if not region:
        pytest.fail("--region is required")
    metadata.insert("region", region)
    return region


@pytest.fixture(scope="class")
def installation_option(metadata, request):
    """
    Test installation option.
    """
    if metadata.get("installation_option"):
        return metadata.get("installation_option")

    installation_option = request.config.getoption("--installation_option")
    if not installation_option:
        installation_option = "kustomize"
    metadata.insert("installation_option", installation_option)

    return installation_option


@pytest.fixture(scope="class")
def deployment_option(metadata, request):
    """
    Test deployment option.
    """
    if metadata.get("deployment_option"):
        return metadata.get("deployment_option")

    deployment_option = request.config.getoption("--deployment_option")
    if not deployment_option:
        deployment_option = "vanilla"
    metadata.insert("deployment_option", deployment_option)

    return deployment_option


@pytest.fixture(scope="class")
def pipeline_s3_credential_option(metadata, request):
    """
    Test credentials option.
    """
    if metadata.get("pipeline_s3_credential_option"):
        return metadata.get("pipeline_s3_credential_option")

    pipeline_s3_credential_option = request.config.getoption(
        "--pipeline_s3_credential_option"
    )
    if not pipeline_s3_credential_option:
        pipeline_s3_credential_option = "static"
    metadata.insert("pipeline_s3_credential_option", pipeline_s3_credential_option)

    return pipeline_s3_credential_option


@pytest.fixture(scope="class")
def root_domain_name(metadata, request):
    cognito_deps = metadata.get("cognito_dependencies")
    if cognito_deps:
        return cognito_deps["route53"]["rootDomain"]["name"]

    return get_root_domain_name(request)


@pytest.fixture(scope="class")
def root_domain_hosted_zone_id(metadata, request):
    cognito_deps = metadata.get("cognito_dependencies")
    if cognito_deps:
        return cognito_deps["route53"]["rootDomain"]["hostedZoneId"]

    return request.config.getoption("--root-domain-hosted-zone-id")
