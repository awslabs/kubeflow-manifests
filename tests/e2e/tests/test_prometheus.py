import pytest

from e2e.utils.prometheus.setup_prometheus_server import *

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import (
    rand_name,
)
from e2e.utils.config import metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster # Needed for kustomize.
from e2e.fixtures.kustomize import (
    kustomize, # Needed for port_forward.
    clone_upstream, # Needed for kustomize.
    configure_manifests, # Needed for kustomize.
)
from e2e.fixtures.clients import (
    kfp_client,
    port_forward, # Needed for kfp_client.
    host, # Needed for kfp_client.
    client_namespace, # Needed for kfp_client.
    session_cookie, # Needed for kfp_client.
    login, # Needed for session_cookie.
    password, # Needed for session_cookie.
)

from kfp_server_api.exceptions import ApiException as KFPApiException

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../docs/deployment/vanilla"

@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH

class TestPrometheus:
    @pytest.fixture(scope="class")
    def setup(self):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestPrometheus", metadata_file)

    def test_set_up_prometheus(self, metadata, region, kustomize):
        global workspace_id
        cluster_name = metadata.get("cluster_name")
        workspace_id = set_up_prometheus_for_AMP(cluster_name, region)
        set_up_prometheus_port_forwarding()
        check_prometheus_is_running()

    def test_pre_kfp_experiment_count(self, region):
        check_AMP_connects_to_prometheus(region, workspace_id, 0)
        
    def test_kfp_experiment(self, kfp_client):
        name = rand_name("experiment-")
        print("PROMETHEUS_PRINT: Created random name.")
        description = rand_name("description-")
        print("PROMETHEUS_PRINT: Created random description.")
        experiment = kfp_client.create_experiment(
            name, description=description, namespace=DEFAULT_USER_NAMESPACE
        )
        print("PROMETHEUS_PRINT: Created a kfp experiment")
        
        assert name == experiment.name
        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert description == experiment.description
        print("PROMETHEUS_PRINT: Asserted the descriptions were equivalent.")
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")

        print("PROMETHEUS_PRINT: First getting the experiment.")
        resp = kfp_client.get_experiment(
            experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
        )

        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert name == resp.name
        print("PROMETHEUS_PRINT: Asserted the descriptions were equivalent.")
        assert description == resp.description
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id

    def test_post_kfp_experiment_count(self, region):
        check_AMP_connects_to_prometheus(region, workspace_id, 1)
            
    def test_clean_up_AMP(self, region):
        # Delete role, policy, and AMP workspace.
        print("PROMETHEUS_PRINT: About to start cleanup")
        delete_AMP_resources(region, workspace_id)
        print("PROMETHEUS_PRINT: Finished cleanup")
