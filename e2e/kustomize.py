

import subprocess
import tempfile
import time

import pytest

from e2e.config import configure_resource_fixture
from e2e.utils import wait_for


def apply_kustomize(path):
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        apply_retcode = subprocess.call(f"kubectl apply -f {tmp.name}".split())
        assert apply_retcode == 0

def delete_kustomize(path):
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        subprocess.call(f"kubectl delete -f {tmp.name}".split())

@pytest.fixture(scope="class")
def kustomize(metadata, cluster, kustomize_path, request):
    def on_create():
        wait_for(lambda : apply_kustomize(kustomize_path), timeout=20*60)
        time.sleep(5*60)    # wait a bit for all pods to be running
        # todo: verify this programmatically
    
    def on_delete():
        delete_kustomize(kustomize_path)

    configure_resource_fixture(metadata, 
                               request, 
                               kustomize_path, 
                               'kustomize_path', 
                               on_create, 
                               on_delete)