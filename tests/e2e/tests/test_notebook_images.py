import subprocess
import pytest

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata, configure_resource_fixture

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.installation import (
    installation,
    clone_upstream,
    configure_manifests,
    ebs_addon,
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
    "kubeflownotebookswg/jupyter-scipy:v1.7.0",
    "public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-tensorflow:2.12.0-gpu-py310-cu118-ubuntu20.04-ec2-v1.0",
    "public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-tensorflow:2.12.0-cpu-py310-ubuntu20.04-ec2-v1.0",
    "public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-pytorch:2.0.0-gpu-py310-cu118-ubuntu20.04-ec2-v1.0",
    "public.ecr.aws/kubeflow-on-aws/notebook-servers/jupyter-pytorch:2.0.0-cpu-py310-ubuntu20.04-ec2-v1.0",
]

testdata = [
    ("scipy", NOTEBOOK_IMAGES[0], "sanity_check.ipynb", "Hello World!"),
    ("tf-gpu", NOTEBOOK_IMAGES[1], "verify_tensorflow_installation.ipynb", "2.12.0"),
    ("tf-cpu", NOTEBOOK_IMAGES[2], "verify_tensorflow_installation.ipynb", "2.12.0"),
    (
        "pytorch-gpu",
        NOTEBOOK_IMAGES[3],
        "verify_pytorch_installation.ipynb",
        "2.0.0",
    ),
    (
        "pytorch-cpu",
        NOTEBOOK_IMAGES[4],
        "verify_pytorch_installation.ipynb",
        "2.0.0",
    ),
]

INSTALLATION_PATH_FILE = "./resources/installation_config/vanilla.yaml"


@pytest.fixture(scope="class")
def installation_path():
    return INSTALLATION_PATH_FILE


class TestNotebookImages:
    @pytest.fixture(scope="function")
    def setup(self, metadata, configure_manifests, installation):
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
