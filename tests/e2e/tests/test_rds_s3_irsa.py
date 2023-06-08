import os
import json
import subprocess

import pytest
import boto3
import yaml


from e2e.utils.utils import (
    wait_for,
    rand_name,
    WaitForCircuitBreakerError,
    unmarshal_yaml,
    get_cfn_client,
    get_ec2_client,
    get_s3_client,
    get_iam_client,
    get_eks_client,
    get_mysql_client,
    load_json_file,
    load_yaml_file,
    exec_shell,
    write_env_to_yaml,
)
from e2e.utils.config import metadata, configure_env_file, configure_resource_fixture

from e2e.conftest import (
    region,
    get_accesskey,
    get_secretkey,
    keep_successfully_created_resource,
)

from e2e.fixtures.cluster import (
    cluster,
    create_iam_service_account,
    associate_iam_oidc_provider,
    delete_iam_service_account,
)
from e2e.fixtures.secrets import aws_secrets_driver, create_secret_string
from e2e.fixtures.installation import installation, clone_upstream, ebs_addon
from e2e.fixtures.clients import (
    kfp_client,
    port_forward,
    account_id,
    session_cookie,
    host,
    login,
    password,
    client_namespace,
    create_k8s_admission_registration_api_client,
)
from e2e.utils import mysql_utils

from e2e.utils.utils import kubectl_apply

from e2e.utils.cloudformation_resources import (
    create_cloudformation_fixture,
    get_stack_outputs,
)
from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from e2e.utils.aws.iam import IAMPolicy


from kfp_server_api.exceptions import ApiException as KFPApiException
from kubernetes.client.exceptions import ApiException as K8sApiException

from e2e.test_methods import rds_s3


TO_ROOT_PATH = "../../"

INSTALLATION_PATH_FILE = "./resources/installation_config/rds-s3.yaml"
RDS_S3_CLOUDFORMATION_TEMPLATE_PATH = (
    "./resources/cloudformation-templates/rds-s3-irsa.yaml"
)
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"
DISABLE_PIPELINE_CACHING_PATCH_FILE = (
    "./resources/custom-resource-templates/patch-disable-pipeline-caching.yaml"
)

DEFAULT_USER_NAMESPACE = "kubeflow-user-example-com"


@pytest.fixture(scope="class")
def installation_path():
    return INSTALLATION_PATH_FILE


@pytest.fixture(scope="class")
def associate_oidc(cluster, region):
    associate_iam_oidc_provider(cluster_name=cluster, region=region)


@pytest.fixture(scope="class")
def cfn_stack(metadata, cluster, region, request):
    cfn_client = get_cfn_client(region)
    ec2_client = get_ec2_client(region)
    stack_name = rand_name("test-e2e-rds-s3-stack-")

    resp = ec2_client.describe_vpcs(
        Filters=[
            {
                "Name": "tag:alpha.eksctl.io/cluster-name",
                "Values": [cluster],
            },
        ],
    )
    vpc_id = resp["Vpcs"][0]["VpcId"]

    resp = ec2_client.describe_subnets(
        Filters=[
            {
                "Name": "tag:alpha.eksctl.io/cluster-name",
                "Values": [cluster],
            },
            {
                "Name": "tag:aws:cloudformation:logical-id",
                "Values": ["SubnetPublic*"],
            },
        ],
    )
    public_subnets = [s["SubnetId"] for s in resp["Subnets"]]

    resp = ec2_client.describe_instances(
        Filters=[
            {
                "Name": "tag:eks:cluster-name",
                "Values": [cluster],
            }
        ],
    )
    instances = [i for r in resp["Reservations"] for i in r["Instances"]]
    security_groups = [i["SecurityGroups"][0]["GroupId"] for i in instances]

    return create_cloudformation_fixture(
        metadata=metadata,
        request=request,
        cfn_client=cfn_client,
        template_path=RDS_S3_CLOUDFORMATION_TEMPLATE_PATH,
        stack_name=stack_name,
        metadata_key="test_rds_s3_cfn_stack",
        create_timeout=10 * 60,
        delete_timeout=10 * 60,
        params={
            "VpcId": vpc_id,
            "Subnets": ",".join(public_subnets),
            "SecurityGroupId": security_groups[0],
            "DBUsername": rand_name("admin"),
            "DBPassword": rand_name("Kubefl0w"),
        },
    )


KFP_MANIFEST_FOLDER = "../../awsconfigs/apps/pipeline"
KFP_RDS_PARAMS_ENV_FILE = f"{KFP_MANIFEST_FOLDER}/rds/params.env"
KFP_S3_PARAMS_ENV_FILE = f"{KFP_MANIFEST_FOLDER}/s3/params.env"

AWS_SECRETS_MANAGER_MANIFEST_FOLDER = "../../awsconfigs/common/aws-secrets-manager"
RDS_SECRET_PROVIDER_CLASS_FILE = (
    f"{AWS_SECRETS_MANAGER_MANIFEST_FOLDER}/rds/secret-provider.yaml"
)

path_dic_rds_s3 = load_yaml_file(INSTALLATION_PATH_FILE)
# pipelines helm path
pipeline_rds_s3_helm_path = path_dic_rds_s3["kubeflow-pipelines"][
    "installation_options"
]["helm"]["paths"]

# secrets-manager helm path
secrets_manager_rds_s3_helm_path = path_dic_rds_s3["aws-secrets-manager"][
    "installation_options"
]["helm"]["paths"]

# pipelines values file
pipeline_rds_s3_values_file = f"{pipeline_rds_s3_helm_path}/values.yaml"

# secrets-manager values file
secrets_manager_rds_s3_values_file = f"{secrets_manager_rds_s3_helm_path}/values.yaml"


METADB_NAME = "metadata_db"


@pytest.fixture(scope="class")
def installation_path():
    return INSTALLATION_PATH_FILE


@pytest.fixture(scope="class")
def associate_oidc(cluster, region):
    associate_iam_oidc_provider(cluster_name=cluster, region=region)


@pytest.fixture(scope="class")
def configure_manifests(cfn_stack, aws_secrets_driver, profile_role, region, cluster):
    cfn_client = get_cfn_client(region)
    stack_outputs = get_stack_outputs(cfn_client, cfn_stack["stack_name"])

    rds_secret_provider = unmarshal_yaml(RDS_SECRET_PROVIDER_CLASS_FILE)
    rds_secret_provider_objects = yaml.safe_load(
        rds_secret_provider["spec"]["parameters"]["objects"]
    )
    rds_secret_provider_objects[0]["objectName"] = "-".join(
        stack_outputs["RDSSecretName"].split(":")[-1].split("-")[:-1]
    )
    rds_secret_provider["spec"]["parameters"]["objects"] = yaml.dump(
        rds_secret_provider_objects
    )

    with open(RDS_SECRET_PROVIDER_CLASS_FILE, "w") as file:
        yaml.dump(rds_secret_provider, file)

    rds_params = {
        "dbHost": stack_outputs["RDSEndpoint"],
        "mlmdDb": METADB_NAME,
    }

    s3_params = {
        "bucketName": stack_outputs["S3BucketName"],
        "minioServiceHost": "s3.amazonaws.com",
        "minioServiceRegion": region,
    }

    configure_env_file(env_file_path=KFP_RDS_PARAMS_ENV_FILE, env_dict=rds_params)

    configure_env_file(env_file_path=KFP_S3_PARAMS_ENV_FILE, env_dict=s3_params)

    write_env_to_yaml(rds_params, pipeline_rds_s3_values_file, module="rds")
    write_env_to_yaml(s3_params, pipeline_rds_s3_values_file, module="s3")

    rds_secret_params = {
        "secretName": "-".join(
            stack_outputs["RDSSecretName"].split(":")[-1].split("-")[:-1]
        )
    }

    write_env_to_yaml(
        rds_secret_params, secrets_manager_rds_s3_values_file, module="rds"
    )

    iam_client = get_iam_client(region=region)
    resp = iam_client.get_role(RoleName=profile_role)
    oidc_role_arn = resp["Role"]["Arn"]

    # kustomize
    CHART_EXPORT_PATH = "../../awsconfigs/apps/pipeline/s3/service-account.yaml"
    USER_NAMESPACE_PATH = "../../awsconfigs/common/user-namespace/overlay/profile.yaml"
    exec_shell(
        f'yq e \'.metadata.annotations."eks.amazonaws.com/role-arn"="{oidc_role_arn}"\' '
        + f"-i {CHART_EXPORT_PATH}"
    )
    exec_shell(
        f'yq e \'.spec.plugins[0].spec."awsIamRole"="{oidc_role_arn}"\' '
        + f"-i {USER_NAMESPACE_PATH}"
    )

    # Helm
    USER_NAMESPACE_PATH = "../../charts/common/user-namespace/values.yaml"
    exec_shell(
        f"yq e '.s3.roleArn=\"{oidc_role_arn}\"' " + f"-i {pipeline_rds_s3_values_file}"
    )
    exec_shell(
        f"yq e '.awsIamForServiceAccount.awsIamRole=\"{oidc_role_arn}\"' "
        + f"-i {USER_NAMESPACE_PATH}"
    )

    os.environ["CLUSTER_REGION"] = region
    os.environ["CLUSTER_NAME"] = cluster


@pytest.fixture(scope="class")
def delete_s3_bucket_contents(cfn_stack, request, region):
    """
    Hack to clean out s3 objects since CFN does not allow deleting non-empty buckets
    nor provides a way to empty a bucket.
    """

    yield

    if keep_successfully_created_resource(request):
        return

    cfn_client = get_cfn_client(region)
    stack_outputs = get_stack_outputs(cfn_client, cfn_stack["stack_name"])

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(stack_outputs["S3BucketName"])
    bucket.objects.delete()


PIPELINE_NAME = "[Demo] XGBoost - Iterative model training"
KATIB_EXPERIMENT_FILE = "katib-experiment-random.yaml"


@pytest.fixture(scope="class")
def profile_trust_policy(cluster, region, account_id, associate_oidc):
    eks_client = get_eks_client(region=region)

    resp = eks_client.describe_cluster(name=cluster)
    oidc_url = resp["cluster"]["identity"]["oidc"]["issuer"].split("https://")[1]

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": f"arn:aws:iam::{account_id}:oidc-provider/{oidc_url}"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{oidc_url}:aud": "sts.amazonaws.com",
                        f"{oidc_url}:sub": [
                            f"system:serviceaccount:kubeflow-user-example-com:default-editor",
                            "system:serviceaccount:kubeflow:ml-pipeline",
                        ],
                    }
                },
            }
        ],
    }

    return json.dumps(trust_policy)


@pytest.fixture(scope="class")
def profile_role(region, metadata, request, profile_trust_policy):
    role_name = rand_name("profile-role-")
    metadata_key = "profile_role_name"

    def on_create():
        iam_client = get_iam_client(region=region)
        iam_client.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=profile_trust_policy
        )

        iam_client.attach_role_policy(
            RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )

    def on_delete():
        name = metadata.get(metadata_key) or role_name
        iam_client = get_iam_client(region=region)
        iam_client.detach_role_policy(
            RoleName=name, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
        iam_client.delete_role(RoleName=name)

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=role_name,
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


class TestRDSS3:
    @pytest.fixture(scope="class")
    def setup(
        self,
        metadata,
        port_forward,
        cluster,
        region,
        delete_s3_bucket_contents,
    ):

        # Disable caching in KFP
        # By default KFP will cache previous pipeline runs and subsequent runs will skip cached steps
        # This prevents artifacts from being uploaded to s3 for subsequent runs
        patch_body = unmarshal_yaml(DISABLE_PIPELINE_CACHING_PATCH_FILE)
        k8s_admission_registration_api_client = (
            create_k8s_admission_registration_api_client(cluster, region)
        )
        k8s_admission_registration_api_client.patch_mutating_webhook_configuration(
            "cache-webhook-kubeflow", patch_body
        )

        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestRDSS3", metadata_file)

    # # todo: make test method reusable
    def test_kfp_experiment(self, setup, kfp_client, cfn_stack, region):
        cfn_client = get_cfn_client(region)
        stack_outputs = get_stack_outputs(cfn_client, cfn_stack["stack_name"])

        db_username = cfn_stack["params"]["DBUsername"]
        db_password = cfn_stack["params"]["DBPassword"]
        rds_endpoint = stack_outputs["RDSEndpoint"]

        rds_s3.test_kfp_experiment(kfp_client, db_username, db_password, rds_endpoint)

    # todo: make test method reusable
    def test_run_pipeline(self, setup, kfp_client, cfn_stack, region):
        cfn_client = get_cfn_client(region)
        stack_outputs = get_stack_outputs(cfn_client, cfn_stack["stack_name"])

        db_username = cfn_stack["params"]["DBUsername"]
        db_password = cfn_stack["params"]["DBPassword"]
        rds_endpoint = stack_outputs["RDSEndpoint"]
        s3_bucket_name = stack_outputs["S3BucketName"]

        rds_s3.test_run_pipeline(
            kfp_client, s3_bucket_name, db_username, db_password, rds_endpoint, region
        )

    # todo: make test method reusable
    def test_katib_experiment(self, setup, cluster, region, cfn_stack):
        cfn_client = get_cfn_client(region)
        stack_outputs = get_stack_outputs(cfn_client, cfn_stack["stack_name"])

        db_username = cfn_stack["params"]["DBUsername"]
        db_password = cfn_stack["params"]["DBPassword"]
        rds_endpoint = stack_outputs["RDSEndpoint"]

        rds_s3.test_katib_experiment(
            cluster, region, db_username, db_password, rds_endpoint
        )
