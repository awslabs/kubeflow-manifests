import pytest
import subprocess
import os
import json

from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
    TO_ROOT,
    CUSTOM_RESOURCE_TEMPLATES_FOLDER,
    KATIB_EXPERIMENT_RANDOM_FILE,
    PIPELINE_DATA_PASSING,
    PIPELINE_SAGEMAKER_TRAINING,
    NOTEBOOK_IMAGE_TF_CPU,
)

from e2e.utils.utils import (
    wait_for,
    rand_name,
    WaitForCircuitBreakerError,
)

from e2e.utils.custom_resources import (
    create_katib_experiment_from_yaml,
    get_katib_experiment,
    delete_katib_experiment,
)

from kfp_server_api.exceptions import ApiException as KFPApiException
from kubernetes.client.exceptions import ApiException as K8sApiException

from e2e.utils.aws.iam import IAMRole
from e2e.utils.s3_for_training.data_bucket import S3BucketWithTrainingData

TEST_ACK_CRDS_PARAMS = [
    (
        "ack",
        NOTEBOOK_IMAGE_TF_CPU,
        "verify_ack_integration.ipynb",
        "No resources found in kubeflow-user-example-com namespace",
    ),
]

TEST_KFP_SM_PARAMS = [
    DEFAULT_USER_NAMESPACE,
]

@pytest.fixture(scope="class")
def sagemaker_execution_role(region):
    role_name = rand_name("sm-exec-role-")

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "sagemaker.amazonaws.com"},
                "Action": "sts:AssumeRole",
            }
        ],
    }

    managed_policies = [
        "arn:aws:iam::aws:policy/AmazonS3FullAccess",
        "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
    ]

    role = IAMRole(name=role_name, region=region, policy_arns=managed_policies)
    role.create(policy_document=json.dumps(trust_policy))

    yield role

    role.delete()


@pytest.fixture(scope="class")
def s3_bucket_with_data():
    bucket_name = rand_name("kfp-sm-training-data-")

    bucket = S3BucketWithTrainingData(name=bucket_name)
    bucket.create()

    yield bucket

    bucket.delete()

@pytest.fixture(scope="function")
def clean_up_training_jobs_in_user_ns(user_namespace):
    yield 

    cmd = f"kubectl delete trainingjobs --all -n {user_namespace}".split()
    subprocess.Popen(cmd)

def wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id):
    def callback():
        resp = kfp_client.get_run(run.id).run

        assert resp.name == job_name
        assert resp.pipeline_spec.pipeline_id == pipeline_id
        assert resp.status == "Succeeded"

    wait_for(callback, 600)


def test_kfp_experiment(kfp_client, user_namespace=DEFAULT_USER_NAMESPACE):
    name = rand_name("experiment-")
    description = rand_name("description-")
    experiment = kfp_client.create_experiment(
        name, description=description, namespace=user_namespace
    )

    assert name == experiment.name
    assert description == experiment.description
    assert user_namespace == experiment.resource_references[0].key.id

    resp = kfp_client.get_experiment(
        experiment_id=experiment.id, namespace=user_namespace
    )

    assert name == resp.name
    assert description == resp.description
    assert user_namespace == resp.resource_references[0].key.id

    kfp_client.delete_experiment(experiment.id)

    try:
        kfp_client.get_experiment(experiment_id=experiment.id, namespace=user_namespace)
        raise AssertionError("Expected KFPApiException Not Found")
    except KFPApiException as e:
        assert "Not Found" == e.reason


def test_run_pipeline(
    kfp_client,
    user_namespace=DEFAULT_USER_NAMESPACE,
    pipeline_name=PIPELINE_DATA_PASSING,
):
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
    assert run.status == None

    wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

    kfp_client.delete_experiment(experiment.id)


def test_katib_experiment(
    cluster,
    region,
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


def test_ack_crds(
    notebook_server,
    framework_name,
    ipynb_notebook_file,
    expected_output,
    user_namespace=DEFAULT_USER_NAMESPACE,
):
    """
    Spins up a DLC Notebook and checks that the basic ACK CRD is installed.
    """
    nb_list = subprocess.check_output(
        f"kubectl get notebooks -n {user_namespace}".split()
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
    print(output)
    # The second condition is now required in case the kfp test runs before this one.
    assert expected_output in output or "training-job-" in output


def test_run_kfp_sagemaker_pipeline(
    kfp_client,
    s3_bucket_with_data,
    sagemaker_execution_role_arn,
    clean_up_training_jobs_in_user_ns,
    user_namespace=DEFAULT_USER_NAMESPACE,
):
    random_prefix = rand_name("kfp-")

    experiment_name = "experiment-" + random_prefix
    experiment_description = "description-" + random_prefix
    bucket_name = s3_bucket_with_data

    job_name = "kfp-run-" + random_prefix

    experiment = kfp_client.create_experiment(
        experiment_name,
        description=experiment_description,
        namespace=user_namespace,
    )

    pipeline_id = kfp_client.get_pipeline_id(PIPELINE_SAGEMAKER_TRAINING)

    params = {
        "sagemaker_role_arn": sagemaker_execution_role_arn,
        "s3_bucket_name": bucket_name,
    }

    run = kfp_client.run_pipeline(
        experiment.id, job_name=job_name, pipeline_id=pipeline_id, params=params
    )

    assert run.name == job_name
    assert run.pipeline_spec.pipeline_id == pipeline_id
    assert run.status == None

    wait_for_run_succeeded(kfp_client, run, job_name, pipeline_id)

    kfp_client.delete_experiment(experiment.id)
