import subprocess
import pytest

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata, configure_resource_fixture, configure_env_file

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, clone_upstream
from e2e.fixtures.profile_dependencies import (
    configure_manifests,
    profile_controller_policy,
    profile_controller_service_account,
    profile_trust_policy,
    profile_role,
    associate_oidc,
    kustomize_path,
)
from e2e.fixtures.clients import (
    account_id,
    kfp_client,
    port_forward,
    session_cookie,
    host,
    login,
    password,
)
from e2e.fixtures.notebook_dependencies import notebook_server

TO_ROOT_PATH = "../../"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"

NOTEBOOK_IMAGES = [
    "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.3-cpu-py38-ubuntu20.04-v1.8",
]

testdata = [
    (
        "ack",
        NOTEBOOK_IMAGES[0],
        "verify_ack_integration.ipynb",
        "No resources found in kubeflow-user-example-com namespace",
    ),
]


class TestACK:
    @pytest.fixture(scope="function")
    def setup(self, metadata, configure_manifests, kustomize):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestACK", metadata_file)

    @pytest.mark.parametrize(
        "framework_name, image_name, ipynb_notebook_file, expected_output", testdata
    )
    def test_ack_crds(
        self,
        setup,
        region,
        metadata,
        notebook_server,
        framework_name,
        image_name,
        ipynb_notebook_file,
        expected_output,
    ):
        """
        Spins up a DLC Notebook and checks that the basic ACK CRD is installed. 
        """
        nb_list = subprocess.check_output(
            f"kubectl get notebooks -n {DEFAULT_USER_NAMESPACE}".split()
        ).decode()

        metadata_key = f"{framework_name}-notebook_server"
        notebook_name = notebook_server["NOTEBOOK_NAME"]
        assert notebook_name is not None
        assert notebook_name in nb_list
        print(notebook_name)

        sub_cmd = f"jupyter nbconvert --to notebook --execute ../uploaded/{ipynb_notebook_file} --stdout"
        cmd = f"kubectl -n kubeflow-user-example-com exec -it {notebook_name}-0 -- /bin/bash -c".split()
        cmd.append(sub_cmd)

        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode()
        print(output)
        assert expected_output in output
