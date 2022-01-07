"""
Installs the vanilla distribution of kubeflow and validates EFS integration by:
    - Installing the EFS Driver from upstream
    - Creating the required IAM Policy, Role and Service Account
    - Creating the EFS Volume 
    - Creating a StorageClass, PersistentVolume and PersistentVolumeClaim using Static Provisioning
"""

import pytest
import subprocess

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster

from e2e.fixtures.kustomize import kustomize, configure_manifests

from e2e.fixtures.storage_efs_dependencies import (
    install_efs_csi_driver,
    create_iam_policy,
    create_efs_volume,
    static_provisioning,
)

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../../../example"


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH


class TestEFS:
    @pytest.fixture(scope="class")
    def setup(self, metadata, kustomize):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestSanity", metadata_file)

    def test_pvc_with_volume(
        self,
        metadata,
        setup,
        install_efs_csi_driver,
        create_iam_policy,
        create_efs_volume,
        static_provisioning,
    ):
        details_efs_deps = metadata.get("efs_deps")
        details_efs_volume = metadata.get("efs_volume")
        details_efs_claim = metadata.get("efs_claim")

        driver_list = subprocess.check_output("kubectl get csidriver".split()).decode()
        assert "efs.csi.aws.com" in driver_list

        pod_list = subprocess.check_output("kubectl get pods -A".split()).decode()
        assert "efs-csi-controller" in pod_list

        sa_account = subprocess.check_output(
            "kubectl describe -n kube-system serviceaccount efs-csi-controller-sa".split()
        ).decode()
        assert details_efs_deps["efs_iam_policy_name"] in sa_account

        fs_id = details_efs_volume["file_system_id"]
        assert "fs-" in fs_id

        claim_name = details_efs_claim["claim_name"]
        claim_list = subprocess.check_output("kubectl get pvc -A".split()).decode()
        assert claim_name in claim_list
