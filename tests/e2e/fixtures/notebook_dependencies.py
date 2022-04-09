import pytest
import subprocess
import boto3
import os
import stat
import sys

from e2e.utils.config import metadata
from e2e.fixtures.kustomize import kustomize, configure_manifests
from e2e.utils.cognito_bootstrap.common import load_cfg, write_cfg
from e2e.conftest import region
from e2e.fixtures.cluster import cluster
from e2e.utils.utils import rand_name
from e2e.utils.config import configure_resource_fixture
from e2e.fixtures.cluster import associate_iam_oidc_provider, create_iam_service_account
from e2e.utils.utils import (
    rand_name,
    wait_for,
    get_iam_client,
    get_eks_client,
    get_ec2_client,
    get_efs_client,
    curl_file_to_path,
    kubectl_apply,
    kubectl_delete,
    kubectl_apply_kustomize,
    kubectl_delete_kustomize,
)


from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
)

NOTEBOOK_IMAGES=["public.ecr.aws/j1r0q0g6/notebooks/notebook-servers/jupyter-scipy:v1.4",
  "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.0-gpu-py38-cu112", 
  "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.0-cpu-py38", 
  "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.9.0-gpu-py38-cu111", 
  "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.9.0-cpu-py38" ]


def get_file_system_id_from_name(efs_client, file_system_name):
    def name_matches(filesystem):
        return filesystem["Name"] == file_system_name

    file_systems = efs_client.describe_file_systems()["FileSystems"]

    file_system = next(filter(name_matches, file_systems))

    return file_system["FileSystemId"]


def wait_on_efs_status(desired_status, efs_client, file_system_id):
    def callback():
        response = efs_client.describe_file_systems(
            FileSystemId=file_system_id,
        )
        filesystem_status = response["FileSystems"][0]["LifeCycleState"]
        print(f"{file_system_id} {filesystem_status} .... waiting")
        assert filesystem_status == desired_status

    wait_for(callback)


@pytest.fixture(scope="class")
def provisioning(metadata, region, request, cluster):
    claim_name = rand_name("efs-claim-auto-dyn-")
    efs_pvc_filepath = (
        "../../docs/deployment/add-ons/storage/efs/dynamic-provisioning/pvc.yaml"
    )
    efs_sc_filepath = (
        "../../docs/deployment/add-ons/storage/efs/dynamic-provisioning/sc.yaml"
    )
    efs_permissions_filepath = (
        "../../docs/deployment/add-ons/storage/notebook-sample/set-permission-job.yaml"
    )
    efs_auto_script_filepath = "utils/auto-efs-setup.py"
    efs_claim_dyn = {}
    efs_client = get_efs_client(region)

    def on_create():
        # Run the automated script to create the EFS Filesystem and the SC
        efs_auto_script_absolute_filepath = os.path.join(
            os.path.abspath(sys.path[0]), "../" + efs_auto_script_filepath
        )

        st = os.stat(efs_auto_script_filepath)
        os.chmod(efs_auto_script_filepath, st.st_mode | stat.S_IEXEC)
        subprocess.call(
            [
                "python",
                efs_auto_script_absolute_filepath,
                "--region",
                region,
                "--cluster",
                cluster,
                "--efs_file_system_name",
                claim_name,
                "--efs_security_group_name",
                claim_name + "sg",
            ]
        )

        file_system_id = get_file_system_id_from_name(efs_client, claim_name)

        # PVC creation is not a part of the script
        # Update the values in the pvc.yaml file
        efs_pvc = load_cfg(efs_pvc_filepath)
        efs_pvc["metadata"]["namespace"] = DEFAULT_USER_NAMESPACE
        efs_pvc["metadata"]["name"] = claim_name
        write_cfg(efs_pvc, efs_pvc_filepath)

        kubectl_apply(efs_pvc_filepath)

        efs_claim_dyn["efs_claim_dyn"] = claim_name
        efs_claim_dyn["file_system_id"] = file_system_id

    def on_delete():
        kubectl_delete(efs_pvc_filepath)
        kubectl_delete(efs_sc_filepath)

        # Get FileSystem_ID
        efs_claim_dyn = metadata.get("efs_claim_dyn") or efs_claim_dyn
        fs_id = efs_claim_dyn["file_system_id"]

        # Delete the Mount Targets
        response = efs_client.describe_mount_targets(
            FileSystemId=fs_id,
        )
        existing_mount_targets = response["MountTargets"]
        for mount_target in existing_mount_targets:
            mount_target_id = mount_target["MountTargetId"]
            efs_client.delete_mount_target(
                MountTargetId=mount_target_id,
            )

        # Delete the Filesystem
        efs_client.delete_file_system(
            FileSystemId=fs_id,
        )
        wait_on_efs_status("deleted", efs_client, fs_id)

    return configure_resource_fixture(
        metadata, request, efs_claim_dyn, "efs_claim_dyn", on_create, on_delete
    )


@pytest.fixture(scope="class")
def create_notebook_pods(metadata, region, request, cluster, provisioning):
    notebook_crd_filepath = "resources/custom-resource-templates/notebook-crd.yaml"
    nb_name = rand_name("nb-instance-")
    ###
    efs_claim_dyn = metadata.get("efs_claim_dyn") or efs_claim_dyn
    claim_name = efs_claim_dyn["efs_claim_dyn"]
    nb_name = claim_name
    ###
    nb_details = {}

    def on_create():
        # Add the filesystem_id to the pv.yaml file
        nb_tf_cpu = load_cfg(notebook_crd_filepath)
        nb_tf_cpu["metadata"]["name"] = nb_name
        nb_tf_cpu["metadata"]["namespace"] = DEFAULT_USER_NAMESPACE
        nb_tf_cpu["spec"]["template"]["spec"]["containers"][0]["image"] = NOTEBOOK_IMAGES[0]
        nb_tf_cpu["spec"]["template"]["spec"]["containers"][0]["volumeMounts"][0]["name"] = claim_name 
        nb_tf_cpu["spec"]["template"]["spec"]["volumes"][0]["name"] = claim_name
        nb_tf_cpu["spec"]["template"]["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] = claim_name
        write_cfg(nb_tf_cpu, notebook_crd_filepath)

        kubectl_apply(notebook_crd_filepath)
        nb_details["nb_name"] = nb_name

    def on_delete():
        kubectl_delete(notebook_crd_filepath)

    return configure_resource_fixture(
        metadata, request, nb_details, "nb_details", on_create, on_delete
    )
