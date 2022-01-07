"""
Kustomize fixture module
"""

import subprocess
import tempfile
import time

import pytest

from e2e.utils.config import configure_resource_fixture
from e2e.utils.utils import wait_for


def apply_kustomize(path):
    """
    Equivalent to:

    while ! kustomize build <PATH> | kubectl apply -f -; do echo "Retrying to apply resources"; sleep 10; done

    but creates a temporary file instead of piping.
    """
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        apply_retcode = subprocess.call(f"kubectl apply -f {tmp.name}".split())
        assert apply_retcode == 0


def delete_kustomize(path):
    """
    Equivalent to:

    kustomize build <PATH> | kubectl delete -f -

    but creates a temporary file instead of piping.
    """
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        subprocess.call(f"kubectl delete -f {tmp.name}".split())


@pytest.fixture(scope="class")
def configure_manifests():
    pass


@pytest.fixture(scope="class")
def kustomize(metadata, cluster, configure_manifests, kustomize_path, request):
    """
    This fixture is created once for each test class.

    Before all tests are run, installs kubeflow using the manifest at `kustomize_path`
    if `kustomize_path` was not provided in the metadata.

    After all tests are run, uninstalls kubeflow using the manifest at `kustomize_path`
    if the flag `--keepsuccess` was not provided as a pytest argument.
    """

    def on_create():
        wait_for(lambda: apply_kustomize(kustomize_path), timeout=20 * 60)
        time.sleep(5 * 60)  # wait a bit for all pods to be running
        # todo: verify this programmatically

    def on_delete():
        delete_kustomize(kustomize_path)

    configure_resource_fixture(
        metadata, request, kustomize_path, "kustomize_path", on_create, on_delete
    )
