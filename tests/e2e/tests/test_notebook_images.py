import subprocess
import pytest

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata, configure_resource_fixture

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, clone_upstream, configure_manifests
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
    "public.ecr.aws/j1r0q0g6/notebooks/notebook-servers/jupyter-scipy:v1.5.0",
    "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.3-gpu-py38-cu112-ubuntu20.04-v1.8",
    "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-tensorflow:2.6.3-cpu-py38-ubuntu20.04-v1.8",
    "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.11.0-gpu-py38-cu115-ubuntu20.04-e3-v1.1",
    "public.ecr.aws/c9e4w0g3/notebook-servers/jupyter-pytorch:1.11.0-cpu-py38-ubuntu20.04-e3-v1.1",
]

testdata = [
    ("scipy", NOTEBOOK_IMAGES[0], "sanity_check.ipynb", "Hello World!"),
    ("tf-gpu", NOTEBOOK_IMAGES[1], "verify_tensorflow_installation.ipynb", "2.6.3"),
    ("tf-cpu", NOTEBOOK_IMAGES[2], "verify_tensorflow_installation.ipynb", "2.6.3"),
    (
        "pytorch-gpu",
        NOTEBOOK_IMAGES[3],
        "verify_pytorch_installation.ipynb",
        "1.11.0+cu115",
    ),
    (
        "pytorch-cpu",
        NOTEBOOK_IMAGES[4],
        "verify_pytorch_installation.ipynb",
        "1.11.0+cpu",
    ),
]

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../deployments/vanilla"

@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH

class TestNotebookImages:
    @pytest.fixture(scope="function")
    def setup(self, metadata, configure_manifests, kustomize):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestNotebookImages", metadata_file)

    @pytest.mark.parametrize(
        "framework_name, image_name, ipynb_notebook_file, expected_output", testdata
    )
    def test_notebook_container(
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
        Runs once for each combination in testdata. Spins up a notebook using the image specified and runs the uploaded python notebook.
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
        assert expected_output in output
