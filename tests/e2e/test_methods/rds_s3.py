import os
import json

import pytest


from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
    TO_ROOT,
    CUSTOM_RESOURCE_TEMPLATES_FOLDER,
    DISABLE_PIPELINE_CACHING_PATCH_FILE,
    KATIB_EXPERIMENT_RANDOM_FILE,
    PIPELINE_XG_BOOST,
    ALTERNATE_MLMDB_NAME,
)
from e2e.utils.utils import (
    wait_for,
    rand_name,
    WaitForCircuitBreakerError,
    unmarshal_yaml,
    get_mysql_client,
    get_s3_client,
)
from e2e.utils.config import metadata

from e2e.conftest import (
    region,
)

from e2e.fixtures.clients import (
    create_k8s_admission_registration_api_client,
)
from e2e.utils import mysql_utils

from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from kfp_server_api.exceptions import ApiException as KFPApiException
from kubernetes.client.exceptions import ApiException as K8sApiException


def wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id):
    def callback():
        resp = kfp_client.get_run(run.id)

        assert resp.run.name == job_name
        assert resp.run.pipeline_spec.pipeline_id == pipeline_id

        if "Failed" == resp.run.status:
            print(resp.run)
            raise WaitForCircuitBreakerError("Pipeline run Failed")

        assert resp.run.status == "Succeeded"

        return resp

    return wait_for(callback, timeout=600)


def wait_for_katib_experiment_succeeded(cluster, region, namespace, name):
    def callback():
        resp = get_katib_experiment(cluster, region, namespace, name)

        assert resp["kind"] == "Experiment"
        assert resp["metadata"]["name"] == name
        assert resp["metadata"]["namespace"] == namespace

        assert resp["status"]["completionTime"] != None
        condition_types = {
            condition["type"] for condition in resp["status"]["conditions"]
        }

        if "Failed" in condition_types:
            print(resp)
            raise WaitForCircuitBreakerError("Katib experiment Failed")

        assert "Succeeded" in condition_types

    wait_for(callback)


# Disable caching in KFP
# By default KFP will cache previous pipeline runs and subsequent runs will skip cached steps
# This prevents artifacts from being uploaded to s3 for subsequent runs
def disable_kfp_caching(cluster, region):
    patch_body = unmarshal_yaml(DISABLE_PIPELINE_CACHING_PATCH_FILE)
    k8s_admission_registration_api_client = (
        create_k8s_admission_registration_api_client(cluster, region)
    )
    k8s_admission_registration_api_client.patch_mutating_webhook_configuration(
        "cache-webhook-kubeflow", patch_body
    )


def test_kfp_experiment(
    kfp_client,
    db_username,
    db_password,
    rds_endpoint,
    user_namespace=DEFAULT_USER_NAMESPACE,
):
    name = rand_name("experiment-")
    description = rand_name("description-")
    experiment = kfp_client.create_experiment(
        name, description=description, namespace=user_namespace
    )

    assert name == experiment.name
    assert description == experiment.description
    assert user_namespace == experiment.resource_references[0].key.id

    mysql_client = get_mysql_client(
        user=db_username,
        password=db_password,
        host=rds_endpoint,
        database="mlpipeline",
    )

    resp = mysql_utils.query(
        mysql_client, f"select * from experiments where Name='{name}'"
    )
    assert len(resp) == 1
    assert resp[0]["Name"] == experiment.name
    assert resp[0]["Description"] == experiment.description
    assert resp[0]["Namespace"] == experiment.resource_references[0].key.id

    resp = kfp_client.get_experiment(
        experiment_id=experiment.id, namespace=user_namespace
    )

    assert name == resp.name
    assert description == resp.description
    assert user_namespace == resp.resource_references[0].key.id

    kfp_client.delete_experiment(experiment.id)

    resp = mysql_utils.query(
        mysql_client, f"select * from experiments where Name='{name}'"
    )
    assert len(resp) == 0

    try:
        kfp_client.get_experiment(experiment_id=experiment.id, namespace=user_namespace)
        raise AssertionError("Expected KFPApiException Not Found")
    except KFPApiException as e:
        assert "Not Found" == e.reason

    mysql_client.close()


def test_run_pipeline(
    kfp_client,
    s3_bucket_name,
    db_username,
    db_password,
    rds_endpoint,
    region,
    user_namespace=DEFAULT_USER_NAMESPACE,
    pipeline_name=PIPELINE_XG_BOOST,
):
    s3_client = get_s3_client(region)

    experiment_name = rand_name("experiment-")
    experiment_description = rand_name("description-")
    experiment = kfp_client.create_experiment(
        experiment_name,
        description=experiment_description,
        namespace=user_namespace,
    )

    pipeline_id = kfp_client.get_pipeline_id(pipeline_name)
    job_name = rand_name("run-")

    run = kfp_client.run_pipeline(
        experiment.id, job_name=job_name, pipeline_id=pipeline_id
    )

    assert run.name == job_name
    assert run.pipeline_spec.pipeline_id == pipeline_id

    resp = wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

    workflow_manifest_json = resp.pipeline_runtime.workflow_manifest
    workflow_manifest = json.loads(workflow_manifest_json)

    s3_artifact_keys = []
    for _, node in workflow_manifest["status"]["nodes"].items():
        if "outputs" not in node:
            continue
        if "artifacts" not in node["outputs"]:
            continue

        for artifact in node["outputs"]["artifacts"]:
            if "s3" not in artifact:
                continue
            s3_artifact_keys.append(artifact["s3"]["key"])

    bucket_objects = s3_client.list_objects_v2(Bucket=s3_bucket_name)
    content_keys = {content["Key"] for content in bucket_objects["Contents"]}

    assert f"pipelines/{pipeline_id}" in content_keys
    for key in s3_artifact_keys:
        assert key in content_keys

    mysql_client = get_mysql_client(
        user=db_username,
        password=db_password,
        host=rds_endpoint,
        database="mlpipeline",
    )

    # todo: also add assert for other tables, https://github.com/awslabs/kubeflow-manifests/issues/327
    resp = mysql_utils.query(
        mysql_client, f"select * from run_details where UUID='{run.id}'"
    )

    assert len(resp) == 1
    assert resp[0]["DisplayName"] == job_name
    assert resp[0]["PipelineId"] == pipeline_id
    assert resp[0]["Conditions"] == "Succeeded"

    kfp_client.delete_experiment(experiment.id)


def test_katib_experiment(
    cluster,
    region,
    db_username,
    db_password,
    rds_endpoint,
    custom_resource_templates_folder=CUSTOM_RESOURCE_TEMPLATES_FOLDER,
    katib_experiment_file=KATIB_EXPERIMENT_RANDOM_FILE,
    user_namespace=DEFAULT_USER_NAMESPACE,
):
    filepath = os.path.abspath(
        os.path.join(custom_resource_templates_folder, katib_experiment_file)
    )

    name = rand_name("katib-random-")
    namespace = user_namespace
    replacements = {"NAME": name, "NAMESPACE": namespace}

    resp = create_katib_experiment_from_yaml(
        cluster, region, filepath, namespace, replacements
    )

    assert resp["kind"] == "Experiment"
    assert resp["metadata"]["name"] == name
    assert resp["metadata"]["namespace"] == namespace

    wait_for_katib_experiment_succeeded(cluster, region, namespace, name)

    mysql_client = get_mysql_client(
        user=db_username,
        password=db_password,
        host=rds_endpoint,
        database="kubeflow",
    )

    resp = mysql_utils.query(
        mysql_client,
        f"select count(*) as count from observation_logs where trial_name like '{name}%'",
    )

    assert resp[0]["count"] > 0

    resp = delete_katib_experiment(cluster, region, namespace, name)

    assert resp["kind"] == "Experiment"
    assert resp["metadata"]["name"] == name
    assert resp["metadata"]["namespace"] == namespace

    try:
        get_katib_experiment(cluster, region, namespace, name)
        raise AssertionError("Expected K8sApiException Not Found")
    except K8sApiException as e:
        assert "Not Found" == e.reason


def test_database_exists(db_username, db_password, rds_endpoint, database_name):
    # will throw exception on connection error (e.g. if DB doesn't exist)
    return get_mysql_client(
        user=db_username,
        password=db_password,
        host=rds_endpoint,
        database=database_name,
    )


def test_verify_kubeflow_db(db_username, db_password, rds_endpoint):
    mysql_client = test_database_exists(
        db_username, db_password, rds_endpoint, "kubeflow"
    )

    resp = mysql_utils.query(mysql_client, f"show tables")
    tables_in_kubeflow_db = {t["Tables_in_kubeflow"] for t in resp}
    expected_tables_in_kubeflow_db = {"observation_logs"}
    assert expected_tables_in_kubeflow_db == tables_in_kubeflow_db


def test_verify_mlpipeline_db(db_username, db_password, rds_endpoint):
    mysql_client = test_database_exists(
        db_username, db_password, rds_endpoint, "mlpipeline"
    )

    resp = mysql_utils.query(mysql_client, f"show tables")
    tables_in_mlpipeline = {t["Tables_in_mlpipeline"] for t in resp}
    expected_tables_in_mlpipeline = {
        "pipelines",
        "resource_references",
        "db_statuses",
        "default_experiments",
        "jobs",
        "tasks",
        "experiments",
        "run_details",
        "run_metrics",
        "pipeline_versions",
    }
    assert expected_tables_in_mlpipeline == tables_in_mlpipeline


def test_verify_mlmdb(db_username, db_password, rds_endpoint, mlmdb_name):
    mysql_client = test_database_exists(
        db_username, db_password, rds_endpoint, mlmdb_name
    )

    resp = mysql_utils.query(mysql_client, f"show tables")
    tables_in_mlmdb = {t[f"Tables_in_{mlmdb_name}"] for t in resp}
    expected_tables_in_mlmdb = {
        "ContextProperty",
        "Execution",
        "ParentType",
        "Type",
        "ParentContext",
        "ArtifactProperty",
        "Event",
        "ExecutionProperty",
        "Context",
        "EventPath",
        "Artifact",
        "MLMDEnv",
        "Association",
        "TypeProperty",
        "Attribution",
    }
    assert expected_tables_in_mlmdb == tables_in_mlmdb


def test_s3_bucket_is_being_used_as_metadata_store(s3_bucket_name, region):
    s3_client = get_s3_client(region)

    bucket_objects = s3_client.list_objects_v2(Bucket=s3_bucket_name)
    content_keys = {content["Key"] for content in bucket_objects["Contents"]}

    found_uploaded_pipelines = False
    for key in content_keys:
        if "pipelines/" in key:
            found_uploaded_pipelines = True

    assert found_uploaded_pipelines == True
