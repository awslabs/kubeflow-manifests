import pytest
import subprocess
import tempfile
import time
import yaml
import json

from e2e.utils.config import metadata
from e2e.conftest import region
from e2e.fixtures.cluster import cluster
from e2e.utils.utils import rand_name
from e2e.utils.config import configure_resource_fixture

from e2e.utils.utils import (
    rand_name,
    unmarshal_yaml,
)
from e2e.utils.k8s_core_api import (
    patch_configmap,
    delete_configmap,
    upload_file_as_configmap,
)


from e2e.utils.constants import DEFAULT_USER_NAMESPACE

TO_ROOT_PATH = "../../"


@pytest.fixture(scope="function")
def notebook_server(
    region, metadata, request, framework_name, image_name, ipynb_notebook_file
):
    metadata_key = f"{framework_name}-notebook_server"
    notebook_name = rand_name(f"{framework_name}-nb-")
    config_map_name = f"{notebook_name}-config-map"
    notebook_file_path = (
        TO_ROOT_PATH + "tests/e2e/resources/notebooks/" + ipynb_notebook_file
    )

    notebook_server_pvc_spec_file = (
        TO_ROOT_PATH + "tests/e2e/resources/custom-resource-templates/notebook-pvc.yaml"
    )
    notebook_server_spec_file = (
        TO_ROOT_PATH + "tests/e2e/resources/custom-resource-templates/notebook-crd.yaml"
    )
    replacements = {
        "REGION": region,
        "NOTEBOOK_NAME": notebook_name,
        "NAMESPACE": DEFAULT_USER_NAMESPACE,
        "IMAGE": image_name,
    }
    notebook_pvc = unmarshal_yaml(
        yaml_file=notebook_server_pvc_spec_file, replacements=replacements
    )
    notebook_server = unmarshal_yaml(
        yaml_file=notebook_server_spec_file, replacements=replacements
    )

    def on_create():
        upload_file_as_configmap(
            namespace=DEFAULT_USER_NAMESPACE,
            configmap_name=config_map_name,
            file_path=notebook_file_path,
        )

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_pvc))))
            tmp.flush()
            subprocess.call(f"kubectl apply -f {tmp.name}".split())

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_server))))
            tmp.flush()
            subprocess.call(f"kubectl apply -f {tmp.name}".split())

        # TODO: Add a waiter here else this tests runs very long.
        time.sleep(6 * 60)  # Wait for notebook to be active

    def on_delete():
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_server))))
            tmp.flush()
            subprocess.call(f"kubectl delete -f {tmp.name}".split())

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_pvc))))
            tmp.flush()
            subprocess.call(f"kubectl delete -f {tmp.name}".split())

        delete_configmap(
            namespace=DEFAULT_USER_NAMESPACE, configmap_name=config_map_name
        )

    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=replacements,
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )
