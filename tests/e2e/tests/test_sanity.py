"""
Installs the vanilla distribution of kubeflow and validates the installation by:
    - Creating, describing, and deleting a KFP experiment
    - Running a pipeline that comes with the default kubeflow installation
    - Creating, describing, and deleting a Katib experiment
"""

import os
import subprocess

import pytest

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.utils import load_yaml_file, wait_for, rand_name, write_yaml_file
from e2e.utils.config import configure_resource_fixture, metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, configure_manifests, clone_upstream
from e2e.fixtures.clients import (
    kfp_client,
    port_forward,
    session_cookie,
    host,
    login,
    password,
    client_namespace,
)

from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from e2e.utils.load_balancer.common import CONFIG_FILE as LB_CONFIG_FILE
from kfp_server_api.exceptions import ApiException as KFPApiException
from kubernetes.client.exceptions import ApiException as K8sApiException


GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../deployments/vanilla"
CUSTOM_RESOURCE_TEMPLATES_FOLDER = "./resources/custom-resource-templates"


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH


PIPELINE_NAME = "[Tutorial] Data passing in python components"
KATIB_EXPERIMENT_FILE = "katib-experiment-random.yaml"


def wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id):
    def callback():
        resp = kfp_client.get_run(run.id).run

        assert resp.name == job_name
        assert resp.pipeline_spec.pipeline_id == pipeline_id
        assert resp.status == "Succeeded"

    wait_for(callback)

@pytest.fixture(scope="class")
def setup_load_balancer(metadata, region, request, cluster, kustomize, root_domain_name, root_domain_hosted_zone_id):
    
    lb_deps = {}
    env_value = os.environ.copy()
    env_value["PYTHONPATH"] = f"{os.getcwd()}/..:" + os.environ.get("PYTHONPATH", "")
    def on_create():
        if not root_domain_name or not root_domain_hosted_zone_id:
            pytest.fail(
                "--root-domain-name and --root-domain-hosted-zone-id required for testing via load balancer"
            )

        subdomain_name = rand_name("platform") + "." + root_domain_name
        lb_config = {
            "cluster": {
                "region": region,
                "name": cluster
            },
            "route53": {
                "rootDomain": {
                    "name": root_domain_name,
                    "hostedZoneId": root_domain_hosted_zone_id,
                },
                "subDomain": {
                    "name": subdomain_name,
                },
            }
        }
        write_yaml_file(lb_config, LB_CONFIG_FILE)

        cmd = "python utils/load_balancer/setup_load_balancer.py".split()
        retcode = subprocess.call(
            cmd, stderr=subprocess.STDOUT, env=env_value
        )
        assert retcode == 0
        lb_deps["config"] = load_yaml_file(LB_CONFIG_FILE)

    def on_delete():
        if metadata.get("lb_deps"):
            cmd = "python utils/load_balancer/lb_resources_cleanup.py".split()
            retcode = subprocess.call(
                cmd, stderr=subprocess.STDOUT, env=env_value
            )
            assert retcode == 0

    return configure_resource_fixture(
        metadata, request, lb_deps, "lb_deps", on_create, on_delete
    )


@pytest.fixture(scope="class")
def host(setup_load_balancer):
    print(setup_load_balancer["config"]["route53"]["subDomain"]["name"])
    host = "https://kubeflow." + setup_load_balancer["config"]["route53"]["subDomain"]["name"]
    return host

@pytest.fixture(scope="class")
def port_forward(kustomize):
    pass

class TestSanity:
    @pytest.fixture(scope="class")
    def setup(self, metadata, host):
        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestSanity", metadata_file)

    def test_kfp_experiment(self, setup, kfp_client):
        name = rand_name("experiment-")
        description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            name, description=description, namespace=DEFAULT_USER_NAMESPACE
        )

        assert name == experiment.name
        assert description == experiment.description
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id

        resp = kfp_client.get_experiment(
            experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
        )

        assert name == resp.name
        assert description == resp.description
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id

        kfp_client.delete_experiment(experiment.id)

        try:
            kfp_client.get_experiment(
                experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE
            )
            raise AssertionError("Expected KFPApiException Not Found")
        except KFPApiException as e:
            assert "Not Found" == e.reason

    def test_run_pipeline(self, setup, kfp_client):
        experiment_name = rand_name("experiment-")
        experiment_description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            experiment_name,
            description=experiment_description,
            namespace=DEFAULT_USER_NAMESPACE,
        )

        pipeline_id = kfp_client.get_pipeline_id(PIPELINE_NAME)
        job_name = rand_name("run-")

        run = kfp_client.run_pipeline(
            experiment.id, job_name=job_name, pipeline_id=pipeline_id
        )

        assert run.name == job_name
        assert run.pipeline_spec.pipeline_id == pipeline_id
        assert run.status == None

        wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

        kfp_client.delete_experiment(experiment.id)

    def test_katib_experiment(self, setup, cluster, region):
        filepath = os.path.abspath(
            os.path.join(CUSTOM_RESOURCE_TEMPLATES_FOLDER, KATIB_EXPERIMENT_FILE)
        )

        name = rand_name("katib-random-")
        namespace = DEFAULT_USER_NAMESPACE
        replacements = {"NAME": name, "NAMESPACE": namespace}

        resp = create_katib_experiment_from_yaml(
            cluster, region, filepath, namespace, replacements
        )

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        resp = get_katib_experiment(cluster, region, namespace, name)

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        resp = delete_katib_experiment(cluster, region, namespace, name)

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        try:
            get_katib_experiment(cluster, region, namespace, name)
            raise AssertionError("Expected K8sApiException Not Found")
        except K8sApiException as e:
            assert "Not Found" == e.reason
