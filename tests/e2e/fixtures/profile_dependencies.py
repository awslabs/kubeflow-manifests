import pytest
import boto3
import yaml
import json

from e2e.utils.constants import DEFAULT_USER_NAMESPACE, KUBEFLOW_NAMESPACE
from e2e.utils.utils import (
    rand_name,
    load_json_file,
    unmarshal_yaml,
    get_iam_client,
    get_eks_client,
)
from e2e.utils.config import metadata, configure_resource_fixture

from e2e.conftest import region

from e2e.fixtures.cluster import (
    cluster,
    create_iam_service_account,
    associate_iam_oidc_provider,
    delete_iam_service_account,
)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       

from e2e.utils.aws.iam import IAMPolicy
from e2e.utils.constants import DEFAULT_USER_NAMESPACE

TO_ROOT_PATH = "../../"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"


@pytest.fixture(scope="class")
def kustomize_path():
    return TO_ROOT_PATH + "tests/e2e/resources/custom-manifests/profile-irsa"


@pytest.fixture(scope="class")
def profile_controller_policy(region, metadata, request):
    policy_name = rand_name("kf-profile-controller-policy-")
    metadata_key = "profile_controller_policy"

    resource_details = {}

    def on_create():
        policy = IAMPolicy(name=policy_name, region=region)
        policy.create(
            policy_document=load_json_file(
                TO_ROOT_PATH
                + "awsconfigs/infra_configs/iam_profile_controller_policy.json"
            )
        )

        resource_details["name"] = policy.name
        resource_details["arn"] = policy.arn

    def on_delete():
        details = metadata.get(metadata_key) or resource_details
        policy = IAMPolicy(arn=details["arn"], region=region)
        policy.wait_for_policy_detachments()
        policy.delete()

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=resource_details,
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )


@pytest.fixture(scope="class")
def associate_oidc(cluster, region):
    associate_iam_oidc_provider(cluster_name=cluster, region=region)


@pytest.fixture(scope="class")
def profile_controller_service_account(
    metadata, cluster, region, associate_oidc, profile_controller_policy, request
):
    metadata_key = "profile_controller_service_account"

    service_account_name = "profiles-controller-service-account"

    def on_create():
        create_iam_service_account(
            service_account_name=service_account_name,
            namespace="kubeflow",
            cluster_name=cluster,
            region=region,
            iam_policy_arns=[profile_controller_policy["arn"]],
        )

    def on_delete():
        delete_iam_service_account(
            service_account_name=service_account_name,
            namespace="kubeflow",
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
def profile_trust_policy(
    cluster, region, account_id, profile_controller_service_account
):
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
                    "system:serviceaccount:ack-system:ack-sagemaker-controller",
                    "system:serviceaccount:ack-system:ack-applicationautoscaling-controller"
                ]
                }
            }
            }
        ]
    }

    return json.dumps(trust_policy)


@pytest.fixture(scope="class")
def profile_role(region, metadata, request, profile_trust_policy):
    role_name = rand_name("profile-role-")
    metadata_key = "profile_role_name"
    policies = ["AmazonS3FullAccess", "AmazonSageMakerFullAccess"]
    iam_client = get_iam_client(region=region)

    def on_create():
        iam_client.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=profile_trust_policy
        )

        for policy in policies:
            iam_client.attach_role_policy(
                RoleName=role_name, PolicyArn=f"arn:aws:iam::aws:policy/{policy}"
            )

    def on_delete():
        name = metadata.get(metadata_key) or role_name
        for policy in policies:
            iam_client.detach_role_policy(
            PolicyArn=policy, RoleName=role_name,
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


@pytest.fixture(scope="class")
def client_namespace(profile_role):
    return "kubeflow-user-example-com"


@pytest.fixture(scope="class")
def login():
    return "test-user@kubeflow.org"


@pytest.fixture(scope="class")
def configure_manifests(profile_role, metadata, request, region, kustomize_path):

    iam_client = get_iam_client(region=region)
    resp = iam_client.get_role(RoleName=profile_role)
    oidc_role_arn = resp["Role"]["Arn"]

    replacements = {
        "profile_role": profile_role,
    }

    def on_create():

        # 1. Edit the profile_iam
        filename = kustomize_path + "/profile_iam.yaml"
        
        profile_yaml_original = unmarshal_yaml(yaml_file=filename)
        profile_yaml = unmarshal_yaml(
            yaml_file=filename,
            replacements={"IAM_ROLE": oidc_role_arn, "NAMESPACE": DEFAULT_USER_NAMESPACE},
        )

        with open(filename, "w") as file:
            file.write(str(yaml.dump(profile_yaml)))

        # 2. Edit kustomization.yaml
        ack_filename = TO_ROOT_PATH + "awsconfigs/common/ack-sagemaker-controller/kustomization.yaml"
        ack_yaml_original = unmarshal_yaml(yaml_file=ack_filename)
        ack_yaml = unmarshal_yaml(
            yaml_file=ack_filename,
            replacements={"ACK_SAGEMAKER_OIDC_ROLE": oidc_role_arn},
        )

        with open(ack_filename, "w") as file:
            file.write(str(yaml.dump(ack_yaml)))

    def on_delete():
        pass

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=replacements,
        metadata_key="configure_manifests",
        on_create=on_create,
        on_delete=on_delete,
    )