"""
Kubeflow Installation fixture module
"""

import subprocess
import tempfile
import time
import pytest
import os
from e2e.conftest import keep_successfully_created_resource

from e2e.utils.config import configure_resource_fixture
from e2e.utils.constants import KUBEFLOW_VERSION
from e2e.utils.utils import (
    wait_for,
    kubectl_delete,
    kubectl_delete_crd,
    kubectl_wait_crd,
    apply_kustomize,
    delete_kustomize,
    create_addon,
    delete_addon,
    rand_name,
)
from e2e.utils.kubeflow_installation import install_kubeflow
from e2e.utils.kubeflow_uninstallation import uninstall_kubeflow

from e2e.fixtures.cluster import (
    associate_iam_oidc_provider,
    create_iam_service_account,
    delete_iam_service_account,
)


@pytest.fixture(scope="class")
def configure_manifests(region, cluster):
    os.environ["CLUSTER_REGION"] = region
    os.environ["CLUSTER_NAME"] = cluster

    associate_iam_oidc_provider(cluster, region)

    apply_retcode = subprocess.call(f"make bootstrap-ack".split(), cwd="../..")
    assert apply_retcode == 0

    yield
    subprocess.call(f"make cleanup-ack-req".split(), cwd="../..")


@pytest.fixture(scope="class")
def clone_upstream():
    upstream_path = "../../upstream"
    if not os.path.isdir(upstream_path):
        retcode = subprocess.call(
            f"git clone --branch {KUBEFLOW_VERSION} https://github.com/kubeflow/manifests.git ../../upstream".split()
        )
        assert retcode == 0
    else:
        print("upstream directory already exists, skipping clone ...")


@pytest.fixture(scope="class")
def ebs_addon(metadata, region, request, account_id, cluster):
    ebs_csi_driver = {}

    def on_create():
        ebs_csi_role_name = rand_name("AmazonEKS_EBS_CSI_DriverRole-")
        policy_name = "AmazonEBSCSIDriverPolicy"
        policy_arn = [f"arn:aws:iam::aws:policy/service-role/{policy_name}"]
        create_iam_service_account(
            "ebs-csi-controller-sa",
            "kube-system",
            cluster,
            region,
            iam_policy_arns=policy_arn,
            iam_role_name=ebs_csi_role_name,
        )
        ebs_csi_driver["role_name"] = ebs_csi_role_name
        ebs_csi_driver["service_account_name"] = "ebs-csi-controller-sa"
        create_addon(
            "aws-ebs-csi-driver", cluster, account_id, ebs_csi_role_name, region
        )
        ebs_csi_driver["addon_name"] = "aws-ebs-csi-driver"
        ebs_csi_driver["addon_account"] = account_id

    def on_delete():
        delete_iam_service_account(
            "ebs-csi-controller-sa", "kube-system", cluster, region
        )
        delete_addon("aws-ebs-csi-driver", cluster, region)

    configure_resource_fixture(
        metadata, request, ebs_csi_driver, "ebs_csi_driver", on_create, on_delete
    )


@pytest.fixture(scope="class")
def installation(
    metadata,
    deployment_option,
    cluster,
    clone_upstream,
    configure_manifests,
    ebs_addon,
    installation_path,
    installation_option,
    pipeline_s3_credential_option,
    request,
):
    """
    This fixture is created once for each test class.

    Before all tests are run, installs kubeflow using the manifest at `kustomize_path`
    if `kustomize_path` was not provided in the metadata.

    After all tests are run, uninstalls kubeflow using the manifest at `kustomize_path`
    if the flag `--keepsuccess` was not provided as a pytest argument.
    """

    def on_create():
        install_kubeflow(
            installation_option,
            deployment_option,
            cluster,
            pipeline_s3_credential_option,
        )

    def on_delete():
        uninstall_kubeflow(
            installation_option, deployment_option, pipeline_s3_credential_option
        )

    configure_resource_fixture(
        metadata, request, installation_path, "installation_path", on_create, on_delete
    )
