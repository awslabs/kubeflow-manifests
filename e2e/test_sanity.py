import pytest

import kfp_server_api

from e2e.constants import GENERIC_KUSTOMIZE_MANIFEST_PATH, DEFAULT_USER_NAMESPACE
from e2e.utils import safe_open, wait_for, rand_name
from e2e.config import metadata, region
from e2e.cluster import cluster
from e2e.kustomize import kustomize
from e2e.clients import k8s_client, kfp_client, port_forward


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH

PIPELINE_NAME = "[Tutorial] DSL - Control structures"

def wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id):
    def callback():
        resp = kfp_client.get_run(run.id).run

        assert resp.name == job_name
        assert resp.pipeline_spec.pipeline_id == pipeline_id
        assert resp.status == 'Succeeded'
    
    wait_for(callback)

class TestSanity:
    @pytest.fixture(scope="class")
    def setup(self, metadata, port_forward):
        metadata_file = metadata.to_file()
        print(metadata.params)
        print("Created metadata file for TestSanity", metadata_file)
        
    def test_create_delete_experiment(self, setup, kfp_client):
        name = rand_name('experiment-')
        description = rand_name('description-')
        experiment = kfp_client.create_experiment(name, description=description, namespace=DEFAULT_USER_NAMESPACE)

        assert name == experiment.name
        assert description == experiment.description
        assert DEFAULT_USER_NAMESPACE == experiment.resource_references[0].key.id

        resp = kfp_client.get_experiment(experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE)

        assert name == resp.name
        assert description == resp.description
        assert DEFAULT_USER_NAMESPACE == resp.resource_references[0].key.id

        kfp_client.delete_experiment(experiment.id)

        try:
            kfp_client.get_experiment(experiment_id=experiment.id, namespace=DEFAULT_USER_NAMESPACE)
            raise AssertionError("Expected kfp_server_api.exceptions.ApiException Not Found")
        except kfp_server_api.exceptions.ApiException as e:
            assert 'Not Found' == e.reason


    def test_run_pipeline(self, setup, kfp_client):
        experiment_name = rand_name('experiment-')
        experiment_description = rand_name('description-')
        experiment = kfp_client.create_experiment(experiment_name, description=experiment_description, namespace=DEFAULT_USER_NAMESPACE)

        pipeline_id = kfp_client.get_pipeline_id(PIPELINE_NAME)
        job_name = rand_name('run-')

        run = kfp_client.run_pipeline(experiment.id, job_name=job_name, pipeline_id=pipeline_id)

        assert run.name == job_name
        assert run.pipeline_spec.pipeline_id == pipeline_id
        assert run.status == None

        wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)
