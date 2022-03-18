import time
import pytest
import subprocess
import boto3
import os, stat, sys

from e2e.utils.config import metadata
from e2e.utils.cognito_bootstrap.common import load_cfg, write_cfg
from e2e.fixtures.kustomize import kustomize, configure_manifests
from e2e.conftest import region
from e2e.fixtures.cluster import cluster
from e2e.fixtures.clients import account_id
from e2e.utils.utils import rand_name
from e2e.utils.config import configure_resource_fixture
from e2e.fixtures.cluster import associate_iam_oidc_provider, create_iam_service_account
from e2e.utils.utils import (
    rand_name,
    wait_for,
    get_iam_client,
    get_eks_client,
    get_ec2_client,
    get_fsx_client,
    kubectl_apply,
    kubectl_delete,
    kubectl_apply_kustomize,
    kubectl_delete_kustomize,
)

from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
    DEFAULT_SYSTEM_NAMESPACE,
)


def get_fsx_dns_name(fsx_client, file_system_id):
    response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
    return response["FileSystems"][0]["DNSName"]


def get_fsx_mount_name(fsx_client, file_system_id):
    response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
    return response["FileSystems"][0]["LustreConfiguration"]["MountName"]


def get_file_system_id_from_name(fsx_client, file_system_name):
    def name_matches(filesystem):
        return filesystem["Name"] == file_system_name

    file_systems = fsx_client.describe_file_systems()["FileSystems"]

    file_system = next(filter(name_matches, file_systems))

    return file_system["FileSystemId"]


@pytest.fixture(scope="class")
def static_provisioning(metadata, region, request, cluster):
    claim_name = rand_name("fsx-claim-")
    fsx_pv_filepath = "../../docs/deployment/add-ons/storage/fsx-for-lustre/static-provisioning/pv.yaml"
    fsx_pvc_filepath = "../../docs/deployment/add-ons/storage/fsx-for-lustre/static-provisioning/pvc.yaml"
    fsx_permissions_filepath = (
        "../../docs/deployment/add-ons/storage/notebook-sample/set-permission-job.yaml"
    )
    fsx_auto_script_filepath = "utils/auto-fsx-setup.py"
    fsx_client = get_fsx_client(region)
    fsx_claim = {}

    def on_create():
        # Run the automated script to create the EFS Filesystem and the SC
        fsx_auto_script_absolute_filepath = os.path.join(
            os.path.abspath(sys.path[0]), "../" + fsx_auto_script_filepath
        )

        st = os.stat(fsx_auto_script_filepath)
        os.chmod(fsx_auto_script_filepath, st.st_mode | stat.S_IEXEC)
        subprocess.call(
            [
                "python",
                fsx_auto_script_absolute_filepath,
                "--region",
                region,
                "--cluster",
                cluster,
                "--fsx_file_system_name",
                claim_name,
                "--fsx_security_group_name",
                claim_name + "sg",
                "--write_to_file",
                "True",
            ]
        )

        with open("fsx-config.txt", "r") as f:
            file_system_id = f.read()
        # file_system_id = get_file_system_id_from_name(fsx_client, claim_name)
        dns_name = get_fsx_dns_name(fsx_client, file_system_id)
        mount_name = get_fsx_mount_name(fsx_client, file_system_id)

        # Add the filesystem_id to the pv.yaml file
        fsx_pv = load_cfg(fsx_pv_filepath)
        fsx_pv["spec"]["csi"]["volumeHandle"] = file_system_id
        fsx_pv["metadata"]["name"] = claim_name
        fsx_pv["spec"]["csi"]["volumeAttributes"]["dnsname"] = dns_name
        fsx_pv["spec"]["csi"]["volumeAttributes"]["mountname"] = mount_name
        write_cfg(fsx_pv, fsx_pv_filepath)

        # Update the values in the pvc.yaml file
        fsx_pvc = load_cfg(fsx_pvc_filepath)
        fsx_pvc["metadata"]["namespace"] = DEFAULT_USER_NAMESPACE
        fsx_pvc["metadata"]["name"] = claim_name
        fsx_pvc["spec"]["volumeName"] = claim_name
        write_cfg(fsx_pvc, fsx_pvc_filepath)

        kubectl_apply(fsx_pv_filepath)
        kubectl_apply(fsx_pvc_filepath)

        fsx_claim["claim_name"] = claim_name
        fsx_claim["file_system_id"] = file_system_id

    def on_delete():
        kubectl_delete(fsx_pvc_filepath)
        kubectl_delete(fsx_pv_filepath)

        details_fsx_volume = metadata.get("fsx_claim") or fsx_claim
        # file_system_id = details_fsx_volume["file_system_id"]

        # fsx_client.delete_file_system(
        #     FileSystemId=file_system_id,
        # )

        # Find a way to delete the security group

    return configure_resource_fixture(
        metadata, request, fsx_claim, "fsx_claim", on_create, on_delete
    )
