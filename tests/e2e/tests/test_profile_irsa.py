import subprocess
import os
import json
import re
import tempfile
import time

import pytest
import boto3
import yaml


from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import (
    rand_name,
    load_json_file,
    unmarshal_yaml,
    get_iam_client,
    get_s3_client,
    get_eks_client,
)
from e2e.utils.config import metadata, configure_resource_fixture

from e2e.conftest import (
    region,
    keep_successfully_created_resource,
)

from e2e.fixtures.cluster import (
    cluster,
    create_iam_service_account,
    associate_iam_oidc_provider,
    delete_iam_service_account,
)
from e2e.fixtures.kustomize import kustomize, clone_upstream
from e2e.fixtures.clients import (
    account_id,
)

from e2e.utils import mysql

from e2e.utils.cloudformation_resources import (
    create_cloudformation_fixture,
    get_stack_outputs,
)
from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from e2e.utils.cognito_bootstrap.aws.iam import IAMPolicy

TO_ROOT_PATH = "../../"

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
                "Condition": {"StringEquals": {f"{oidc_url}:aud": "sts.amazonaws.com"}},
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


@pytest.fixture(scope="class")
def configure_manifests(profile_role, region, kustomize_path):

    iam_client = get_iam_client(region=region)
    resp = iam_client.get_role(RoleName=profile_role)
    oidc_role_arn = resp["Role"]["Arn"]

    filename = kustomize_path + "/profile_iam.yaml"

    profile_yaml_original = unmarshal_yaml(yaml_file=filename)
    profile_yaml = unmarshal_yaml(
        yaml_file=filename, replacements={"IAM_ROLE": oidc_role_arn}
    )

    with open(filename, "w") as file:
        file.write(str(yaml.dump(profile_yaml)))

    yield

    with open(filename, "w") as file:
        file.write(str(yaml.dump(profile_yaml_original)))


def upload_file_as_configmap(namespace, configmap_name, file_path):
    subprocess.call(
        f"kubectl create configmap -n {namespace} {configmap_name} --from-file {file_path}".split()
    )


def delete_configmap(namespace, configmap_name):
    subprocess.call(f"kubectl delete configmap -n {namespace} {configmap_name}".split())


class TestProfileIRSA:
    @pytest.fixture(scope="class")
    def setup(self, metadata, configure_manifests, kustomize):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestProfileIRSA", metadata_file)

    @pytest.fixture(scope="class")
    def notebook_server(self, setup, region, metadata, request):
        metadata_key = "notebook_server"

        s3_bucket_name = rand_name("test-profile-irsa-bucket")
        notebook_file_path = (
            TO_ROOT_PATH
            + "docs/component-guides/samples/profiles-irsa/verify_notebook.ipynb"
        )

        notebook_server_pvc_spec_file = (
            TO_ROOT_PATH
            + "tests/e2e/resources/custom-resource-templates/profile-irsa-notebook-pvc.yaml"
        )
        notebook_server_spec_file = (
            TO_ROOT_PATH
            + "tests/e2e/resources/custom-resource-templates/profile-irsa-notebook-server.yaml"
        )
        replacements = {"S3_BUCKET_NAME": s3_bucket_name, "REGION": region}
        notebook_server = unmarshal_yaml(
            yaml_file=notebook_server_spec_file, replacements=replacements
        )

        def on_create():
            upload_file_as_configmap(
                namespace="profile-aws-iam",
                configmap_name="irsa-notebook-as-configmap",
                file_path=notebook_file_path,
            )

            subprocess.call(f"kubectl apply -f {notebook_server_pvc_spec_file}".split())

            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(str.encode(str(yaml.dump(notebook_server))))
                tmp.flush()
                subprocess.call(f"kubectl apply -f {tmp.name}".split())

            time.sleep(3 * 60)  # Wait for notebook to be active

        def on_delete():
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(str.encode(str(yaml.dump(notebook_server))))
                tmp.flush()
                subprocess.call(f"kubectl delete -f {tmp.name}".split())

            subprocess.call(
                f"kubectl delete -f {notebook_server_pvc_spec_file}".split()
            )

            delete_configmap(
                namespace="profile-aws-iam", configmap_name="irsa-notebook-as-configmap"
            )

        return configure_resource_fixture(
            metadata=metadata,
            request=request,
            resource_details=replacements,
            metadata_key=metadata_key,
            on_create=on_create,
            on_delete=on_delete,
        )

    """
    Runs a notebook that will create a S3 bucket as longs as IRSA permissions have been applied. The test will verify IRSA is workings by verifying the S3 bucket was able to be created.
    """

    def test_notebook_irsa(self, notebook_server, region):
        bucket_name = notebook_server["S3_BUCKET_NAME"]
        s3_client = get_s3_client(region=region)

        sub_cmd = "jupyter nbconvert --to notebook --execute ../uploaded/verify_notebook.ipynb --stdout"
        cmd = "kubectl -n profile-aws-iam exec -it test-notebook-irsa-0 -- /bin/bash -c".split()
        cmd.append(sub_cmd)

        subprocess.call(cmd)

        resp = s3_client.list_buckets()
        buckets = {bucket["Name"] for bucket in resp["Buckets"]}

        assert bucket_name in buckets

        s3_client.delete_bucket(Bucket=bucket_name)
