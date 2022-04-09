"""
Tests the Kubeflow Notebook Images by creating a Notebook pod with each of the 4 images
"""

import pytest
import subprocess

from e2e.utils.config import metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.clients import (
    account_id,
    create_k8s_admission_registration_api_client,
    kfp_client,
    host,
    port_forward,
    client_namespace,
    session_cookie,
    login,
    password,
    patch_kfp_to_disable_cache,
)

from e2e.fixtures.kustomize import kustomize, configure_manifests, clone_upstream

from e2e.fixtures.notebook_dependencies import (
    create_notebook_pods,
    provisioning,
)
from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
    DEFAULT_SYSTEM_NAMESPACE,
)
from e2e.utils.utils import (
    unmarshal_yaml,
    rand_name,
    wait_for_kfp_run_succeeded_from_run_id,
)
from e2e.utils.custom_resources import get_pvc_status, get_service_account, get_pod_from_label

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../docs/deployment/vanilla"
DISABLE_PIPELINE_CACHING_PATCH_FILE = (
    "./resources/custom-resource-templates/patch-disable-pipeline-caching.yaml"
)


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH


class TestFSx:
    @pytest.fixture(scope="class")
    def setup(self, metadata, kustomize, patch_kfp_to_disable_cache, port_forward, create_notebook_pods):

        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestFSx_Static", metadata_file)

    def test_pvc_with_volume(
        self,
        metadata,
        account_id,
        setup,
        kfp_client,
        provisioning,
        create_notebook_pods,
    ):
        nb_list = subprocess.check_output(f"kubectl get notebooks -n {DEFAULT_USER_NAMESPACE}".split()).decode()

        nb_name = create_notebook_pods["nb_name"]
        assert nb_name is not None
        assert nb_name in nb_list

        # name, status = get_pod_from_label(cluster, region, DEFAULT_SYSTEM_NAMESPACE, "app","fsx-csi-controller")
        # assert "fsx-csi-controller" in name
        # assert status == "Running"

        


