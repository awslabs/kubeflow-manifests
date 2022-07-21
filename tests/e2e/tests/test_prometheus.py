import pytest

from e2e.utils.prometheus.setup_prometheus_server import *

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import (
    rand_name,
)
from e2e.utils.config import (
    metadata,
    configure_resource_fixture,
)
from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
)

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

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../deployments/vanilla"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"
KATIB_EXPERIMENT_FILE = "katib-experiment-random.yaml"

@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH

@pytest.fixture(scope="class")
def prometheus_amp(request, metadata, region, kustomize):
    metadata_key = "prometheus-amp"
    resource_details = {}

    def on_create():
        cluster_name = metadata.get("cluster_name")
        print("PROMETHEUS_PRINT: Setting up the workspace id in the fixture.")
        workspace_id = set_up_prometheus_for_AMP(cluster_name, region)
        print("PROMETHEUS_PRINT: Setting the workspace_id in the fixture.")
        resource_details["workspace_id"] = workspace_id
        print("PROMETHEUS_PRINT: Finished on_create of fixture.")
        
    def on_delete():
        print("PROMETHEUS_PRINT: Entered on-delete function of fixture.")
        details = metadata.get(metadata_key)
        cluster_name = metadata.get("cluster_name")
        delete_AMP_resources(cluster_name, region, details["workspace_id"])

        print("PROMETHEUS_PRINT: Finished on-delete function of fixture.")
        
    return configure_resource_fixture(
        metadata=metadata,
        request=request,
        resource_details=resource_details,
        metadata_key=metadata_key,
        on_create=on_create,
        on_delete=on_delete,
    )

class TestPrometheus:
    @pytest.fixture(scope="class")
    def setup(self, metadata, prometheus_amp):
        print("PROMETHEUS_PRINT: Starting setup.")
        global workspace_id
        print("PROMETHEUS_PRINT: Made global workspace_id.")
        details = prometheus_amp
        print("PROMETHEUS_PRINT: Got details from metadata.")
        workspace_id = details["workspace_id"]
        print("PROMETHEUS_PRINT: Got workspace_id from details.")
        port_forwarding_process = set_up_prometheus_port_forwarding()
        print("PROMETHEUS_PRINT: Finished setting up port forwarding.")
        
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestPrometheus", metadata_file)
        yield
        port_forwarding_process.terminate()

    def test_set_up_prometheus(self, setup):
        print("PROMETHEUS_PRINT: Checking prometheus is running.")
        check_prometheus_is_running()

    def test_kfp_experiment(self, setup, region, kfp_client):
        prometheus_kfp_experiment_count_query = "experiment_server_create_requests"
        initial_experiment_count = int(get_create_experiment_count(prometheus_kfp_experiment_count_query))

        name = rand_name("experiment-")
        description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            name, description=description, namespace=DEFAULT_USER_NAMESPACE
        )
        print("PROMETHEUS_PRINT: Created a kfp experiment")
        
        assert name == experiment.name
        assert description == experiment.description
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id

        resp = kfp_client.get_experiment(
            experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
        )
        print("PROMETHEUS_PRINT: Finished performing a GET on the KFP experiment.")

        assert name == resp.name
        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert description == resp.description
        print("PROMETHEUS_PRINT: Asserted the descriptions were equivalent.")
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")

        print(f"PROMETHEUS_PRINT: About to check the post-create kfp experiment count, and see if it matches {initial_experiment_count + 1}")
        check_AMP_connects_to_prometheus(region, workspace_id, initial_experiment_count + 1, prometheus_kfp_experiment_count_query)

    def test_katib_experiment(self, cluster, region):
        ## This is the number of get_katib_experiments that have been created.
        prometheus_katib_experiment_count_query = 'rest_client_requests_total\{code="403",job="katib-controller"\}'
        initial_experiment_count = int(get_create_experiment_count(prometheus_katib_experiment_count_query))
        
        filepath = os.path.abspath(
            os.path.join(CUSTOM_RESOURCE_TEMPLATES_FOLDER, KATIB_EXPERIMENT_FILE)
        )
        
        name = rand_name("katib-random-")
        namespace = DEFAULT_USER_NAMESPACE
        replacements = {"NAME": name, "NAMESPACE": namespace}
        
        resp = create_katib_experiment_from_yaml(
            cluster, region, filepath, namespace, replacements
        )
        print("PROMETHEUS_PRINT: Created a katib experiment")
        
        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        resp = get_katib_experiment(cluster, region, namespace, name)
        print("PROMETHEUS_PRINT: Finished performing a GET on the KFP experiment.")
        
        assert resp["kind"] == "Experiment"
        print("PROMETHEUS_PRINT: Asserted the GET returned an Experiment.")
        assert resp["metadata"]["name"] == name
        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert resp["metadata"]["namespace"] == namespace
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")
        
        print(f"PROMETHEUS_PRINT: About to check the post-create katib experiment count, and see if it matches {initial_experiment_count + 1}")
        check_AMP_connects_to_prometheus(region, workspace_id, initial_experiment_count + 1, prometheus_katib_experiment_count_query)
