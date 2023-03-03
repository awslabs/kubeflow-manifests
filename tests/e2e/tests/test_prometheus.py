import pytest
import yaml
import os

from e2e.utils.prometheus.setup_prometheus_server import *

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import (
    rand_name,
    unmarshal_yaml,
)
from e2e.utils.config import (
    metadata,
    configure_resource_fixture,
)
from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
)
from e2e.utils.k8s_core_api import (
    upload_file_as_configmap,
    delete_configmap,
)

from e2e.conftest import region

from e2e.fixtures.cluster import cluster # Needed for kustomize.
from e2e.fixtures.installation import (
    installation, # Needed for port_forward.
    clone_upstream, # Needed for kustomize.
    configure_manifests, # Needed for kustomize.
    ebs_addon
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

INSTALLATION_PATH_FILE = "./resources/installation_config/vanilla.yaml"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"
KATIB_EXPERIMENT_FILE = "katib-experiment-random.yaml"
TO_ROOT_PATH = "../../"

istio_central_dashboard_request_count_query = 'istio_requests_total'\
'\\{destination_app="centraldashboard",response_code="200"\\}'

@pytest.fixture(scope="class")
def installation_path():
    return INSTALLATION_PATH_FILE

@pytest.fixture(scope="class")
def prometheus_amp(request, metadata, region, installation):
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
        global initial_istio_central_dashboard_request_count

        details = prometheus_amp
        print("PROMETHEUS_PRINT: Got details from metadata.")
        workspace_id = details["workspace_id"]
        print("PROMETHEUS_PRINT: Got workspace_id from details.")
        port_forwarding_process = set_up_prometheus_port_forwarding()
        print("PROMETHEUS_PRINT: Finished setting up port forwarding.")

        query_results = get_prometheus_query_results(
            istio_central_dashboard_request_count_query)
        if "result" == query_results:
            initial_istio_central_dashboard_request_count = 0
        else:
            initial_istio_central_dashboard_request_count = int(query_results)
        print(f'PROMETHEUS_PRINT: Got Initial value of the prometheus query: '\
              f'{istio_central_dashboard_request_count_query} = '\
              f'{initial_istio_central_dashboard_request_count}')
        
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestPrometheus", metadata_file)
        yield
        port_forwarding_process.terminate()

    def test_set_up_prometheus(self, setup):
        print("PROMETHEUS_PRINT: Checking prometheus is running.")
        check_prometheus_is_running()

    def test_istio_request_count(self, setup, region, kfp_client):
        # This query returns the number of successfull (code 200)
        # requests the istio ingress gateway makes to the central
        # dashboard.
        # Such a request is made during the creation in the kfp_client
        # fixture.
        print(f"PROMETHEUS_PRINT: About to check the post-create istio request "\
              f"count, and see if it matches "\
              f"{initial_istio_central_dashboard_request_count + 1}")
        check_AMP_connects_to_prometheus(
            region, workspace_id,
            initial_istio_central_dashboard_request_count + 1,
            istio_central_dashboard_request_count_query)
        
    def test_kfp_experiment(self, setup, region, kfp_client):
        # This query returns the number of kfp experiments that have
        # been created.
        prometheus_kfp_experiment_count_query = 'experiment_server_create_requests'\
                                                '\\{job="ml-pipeline"\\}'
        initial_kfp_experiment_count = int(
            get_prometheus_query_results(
                prometheus_kfp_experiment_count_query))

        name = rand_name("experiment-")
        description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            name,
            description=description,
            namespace=DEFAULT_USER_NAMESPACE
        )
        print("PROMETHEUS_PRINT: Created a kfp experiment")
        
        assert name == experiment.name
        assert description == experiment.description
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id

        resp = kfp_client.get_experiment(
            experiment_id=experiment.id,
            namespace=DEFAULT_USER_NAMESPACE
        )
        print("PROMETHEUS_PRINT: Finished performing a GET on the KFP "\
              "experiment.")

        assert name == resp.name
        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert description == resp.description
        print("PROMETHEUS_PRINT: Asserted the descriptions were equivalent.")
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")

        print(f"PROMETHEUS_PRINT: About to check the post-create kfp experiment "\
              "count, and see if it matches {initial_kfp_experiment_count + 1}")
        check_AMP_connects_to_prometheus(
            region, workspace_id,
            initial_kfp_experiment_count + 1,
            prometheus_kfp_experiment_count_query)

    def test_katib_experiment(self, cluster, region):
        # This query returns the number of katib experiments that have
        # been created.
        prometheus_katib_experiment_count_query = 'katib_experiment_created_total'\
                                                  '\\{job="katib-controller"\\}'

        query_results = get_prometheus_query_results(
            prometheus_katib_experiment_count_query)
        if "result" == query_results:
            initial_katib_experiment_count = 0
        else:
            initial_katib_experiment_count = int(query_results)
        
        filepath = os.path.abspath(
            os.path.join(
                CUSTOM_RESOURCE_TEMPLATES_FOLDER,
                KATIB_EXPERIMENT_FILE)
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
        print("PROMETHEUS_PRINT: Finished performing a GET on the KFP "\
              "experiment.")
        
        assert resp["kind"] == "Experiment"
        print("PROMETHEUS_PRINT: Asserted the GET returned an Experiment.")
        assert resp["metadata"]["name"] == name
        print("PROMETHEUS_PRINT: Asserted the names were equivalent.")
        assert resp["metadata"]["namespace"] == namespace
        print("PROMETHEUS_PRINT: Asserted the namespaces were equivalent.")
        
        print(f"PROMETHEUS_PRINT: About to check the post-create katib "\
              f"experiment count, and see if it matches "\
              f"{initial_katib_experiment_count + 1}")
        check_AMP_connects_to_prometheus(
            region, workspace_id,
            initial_katib_experiment_count + 1,
            prometheus_katib_experiment_count_query)

    def test_notebook(self, cluster, region):
        # This query returns the number of notebooks that have been
        # created in the profile-aws-iam namespace.
        prometheus_notebook_count_query = 'notebook_create_total'\
                                          '\\{namespace="profile-aws-iam"\\}'

        query_results = get_prometheus_query_results(
            prometheus_notebook_count_query)
        if "result" == query_results:
            initial_notebook_count = 0
        else:
            initial_notebook_count = int(query_results)

        subprocess.call(f"kubectl create namespace profile-aws-iam".split())

        s3_bucket_name = rand_name("test-profile-irsa-bucket")
        notebook_file_path = (
            TO_ROOT_PATH
            + "deployments/samples/notebooks/verify_profile_iam_notebook.ipynb"
        )
        notebook_server_pvc_spec_file = (
            TO_ROOT_PATH
            + "tests/e2e/resources/custom-resource-templates/"\
            "profile-irsa-notebook-pvc.yaml"
        )
        notebook_server_spec_file = (
            TO_ROOT_PATH
            + "tests/e2e/resources/custom-resource-templates"\
            "/profile-irsa-notebook-server.yaml"
        )
        replacements = {"S3_BUCKET_NAME": s3_bucket_name, "REGION": region}
        notebook_server = unmarshal_yaml(
            yaml_file=notebook_server_spec_file,
            replacements=replacements
        )
        
        upload_file_as_configmap(
            namespace="profile-aws-iam",
            configmap_name="irsa-notebook-as-configmap",
            file_path=notebook_file_path,
        )
        
        subprocess.call(
            f"kubectl apply -f {notebook_server_pvc_spec_file}".split()
        )
        
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_server))))
            tmp.flush()
            subprocess.call(f"kubectl apply -f {tmp.name}".split())
            
            time.sleep(3 * 60)  # Wait for notebook to be active

        print("PROMETHEUS_PRINT: Created a jupyter notebook")

        print(f"PROMETHEUS_PRINT: About to check the post-create notebook "\
              f"count, and see if it matches {initial_notebook_count + 1}")
        check_AMP_connects_to_prometheus(
            region, workspace_id,
            initial_notebook_count + 1,
            prometheus_notebook_count_query)

        print("PROMETHEUS_PRINT: About to delete the jupyter notebook")

        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(str.encode(str(yaml.dump(notebook_server))))
            tmp.flush()
            subprocess.call(f"kubectl delete -f {tmp.name}".split())
            
        subprocess.call(
            f"kubectl delete -f {notebook_server_pvc_spec_file}".split()
        )
        
        delete_configmap(
            namespace="profile-aws-iam",
            configmap_name="irsa-notebook-as-configmap"
        )
