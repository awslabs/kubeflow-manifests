"""
Installs the vanilla distribution of kubeflow and validates EFS integration by:
    - Installing the EFS Driver from upstream
    - Creating the required IAM Policy, Role and Service Account
    - Creating the EFS Volume 
    - Creating a StorageClass, PersistentVolume and PersistentVolumeClaim using Static Provisioning
    - Using KFP to check that the EFS can be accessed
"""

import pytest
import json
import os
import time
import subprocess

from e2e.utils.constants import DEFAULT_USER_NAMESPACE
from e2e.utils.config import metadata

from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.clients import (
    account_id,
    create_k8s_admission_registration_api_client,
    port_forward,
    kfp_client,
    host,
    client_namespace,
    session_cookie,
    login,
    password,
)

from e2e.fixtures.kustomize import kustomize, configure_manifests, clone_upstream

from e2e.fixtures.storage_efs_dependencies import (
    install_efs_csi_driver,
    create_efs_driver_sa,
    create_efs_volume,
    static_provisioning,
    dynamic_provisioning,
)
from e2e.utils.constants import (
    DEFAULT_USER_NAMESPACE,
    DEFAULT_SYSTEM_NAMESPACE,
)
from e2e.utils.utils import (
    unmarshal_yaml,
    rand_name,
    wait_for_kfp_run_succeeded_from_run_id,
)
from e2e.resources.pipelines.pipeline_read_from_volume import read_from_volume_pipeline
from e2e.resources.pipelines.pipeline_write_to_volume import write_to_volume_pipeline

GENERIC_KUSTOMIZE_MANIFEST_PATH = "../../docs/deployment/vanilla"
DISABLE_PIPELINE_CACHING_PATCH_FILE = (
    "./resources/custom-resource-templates/patch-disable-pipeline-caching.yaml"
)
MOUNT_PATH = "/home/jovyan/"


@pytest.fixture(scope="class")
def kustomize_path():
    return GENERIC_KUSTOMIZE_MANIFEST_PATH


class TestEFS_Static:
    @pytest.fixture(scope="class")
    def setup(self, metadata, kustomize, port_forward, static_provisioning):
        # Disable caching in KFP
        # By default KFP will cache previous pipeline runs and subsequent runs will skip cached steps
        # This prevents artifacts from being uploaded to s3 for subsequent runs
        patch_body = unmarshal_yaml(DISABLE_PIPELINE_CACHING_PATCH_FILE)
        k8s_admission_registration_api_client = (
            create_k8s_admission_registration_api_client(cluster, region)
        )
        k8s_admission_registration_api_client.patch_mutating_webhook_configuration(
            "cache-webhook-kubeflow", patch_body
        )

        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestEFS_Static", metadata_file)

    def test_pvc_with_volume(
        self,
        metadata,
        setup,
        kfp_client,
        account_id,
        create_efs_volume,
        static_provisioning,
    ):
        driver_list = subprocess.check_output("kubectl get csidriver".split()).decode()
        assert "efs.csi.aws.com" in driver_list

        pod_list = subprocess.check_output("kubectl get pods -A".split()).decode()
        assert "efs-csi-controller" in pod_list

        sa_account = subprocess.check_output(
            "kubectl describe -n kube-system serviceaccount efs-csi-controller-sa".split()
        ).decode()
        assert f"arn:aws:iam::{account_id}:role" in sa_account

        fs_id = create_efs_volume["file_system_id"]
        assert "fs-" in fs_id

        CLAIM_NAME = static_provisioning["claim_name"]
        print(f"static claim name is {CLAIM_NAME}")
        claim_list = subprocess.check_output("kubectl get pvc -A".split()).decode()
        assert CLAIM_NAME in claim_list

        claim_entry = subprocess.check_output(
            f"kubectl get pvc -n {DEFAULT_USER_NAMESPACE} {CLAIM_NAME} -o=jsonpath='{{.status.phase}}'".split()
        ).decode()
        assert "Bound" in claim_entry

        # TODO: The following can be put into a method or split this into different tests
        # TODO: The following section needs more assertions
        # Create two Pipelines both mounted with the same EFS volume claim.
        # The first one writes a file to the volume, the second one reads it and verifies content.
        experiment_name = rand_name("static-experiment-")
        experiment_description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            experiment_name,
            description=experiment_description,
            namespace=DEFAULT_USER_NAMESPACE,
        )
        arguments = {"mount_path": MOUNT_PATH, "claim_name": CLAIM_NAME}

        # Write Pipeline Run
        write_run_id = kfp_client.create_run_from_pipeline_func(
            write_to_volume_pipeline,
            experiment_name=experiment_name,
            namespace=DEFAULT_USER_NAMESPACE,
            arguments=arguments,
        ).run_id
        print(f"write_pipeline run id is {write_run_id}")
        wait_for_kfp_run_succeeded_from_run_id(kfp_client, write_run_id)

        # Read Pipeline Run
        read_run_id = kfp_client.create_run_from_pipeline_func(
            read_from_volume_pipeline,
            experiment_name=experiment_name,
            namespace=DEFAULT_USER_NAMESPACE,
            arguments=arguments,
        ).run_id
        print(f"read_pipeline run id is {read_run_id}")
        wait_for_kfp_run_succeeded_from_run_id(kfp_client, read_run_id)


class TestEFS_Dynamic:
    @pytest.fixture(scope="class")
    def setup_dynamic(self, metadata, kustomize, port_forward, dynamic_provisioning):
        # Disable caching in KFP
        # By default KFP will cache previous pipeline runs and subsequent runs will skip cached steps
        # This prevents artifacts from being uploaded to s3 for subsequent runs
        patch_body = unmarshal_yaml(DISABLE_PIPELINE_CACHING_PATCH_FILE)
        k8s_admission_registration_api_client = (
            create_k8s_admission_registration_api_client(cluster, region)
        )
        k8s_admission_registration_api_client.patch_mutating_webhook_configuration(
            "cache-webhook-kubeflow", patch_body
        )

        metadata_file = metadata.to_file()
        print(metadata.params)  # These needed to be logged
        print("Created metadata file for TestEFS_Dynamic", metadata_file)

    def test_pvc_with_volume_dynamic(
        self,
        metadata,
        setup_dynamic,
        kfp_client,
        account_id,
        dynamic_provisioning,
    ):
        driver_list = subprocess.check_output("kubectl get csidriver".split()).decode()
        assert "efs.csi.aws.com" in driver_list

        pod_list = subprocess.check_output("kubectl get pods -A".split()).decode()
        assert "efs-csi-controller" in pod_list

        sa_account = subprocess.check_output(
            "kubectl describe -n kube-system serviceaccount efs-csi-controller-sa".split()
        ).decode()
        assert f"arn:aws:iam::{account_id}:role" in sa_account

        fs_id = dynamic_provisioning["file_system_id"]
        assert "fs-" in fs_id

        CLAIM_NAME = dynamic_provisioning["efs_claim_dyn"]
        claim_list = subprocess.check_output("kubectl get pvc -A".split()).decode()
        assert CLAIM_NAME in claim_list

        claim_entry = subprocess.check_output(
            f"kubectl get pvc -n {DEFAULT_USER_NAMESPACE} {CLAIM_NAME} -o=jsonpath='{{.status.phase}}'".split()
        ).decode()
        assert "Pending" in claim_entry

        # TODO: The following can be put into a method or split this into different tests
        # TODO: The following section needs more assertions
        # Create two Pipelines both mounted with the same EFS volume claim.
        # The first one writes a file to the volume, the second one reads it and verifies content.
        experiment_name = rand_name("dyn-experiment-")
        experiment_description = rand_name("description-")
        experiment = kfp_client.create_experiment(
            experiment_name,
            description=experiment_description,
            namespace=DEFAULT_USER_NAMESPACE,
        )
        arguments = {"mount_path": MOUNT_PATH, "claim_name": CLAIM_NAME}

        # Write Pipeline Run
        write_run_id = kfp_client.create_run_from_pipeline_func(
            write_to_volume_pipeline,
            experiment_name=experiment_name,
            namespace=DEFAULT_USER_NAMESPACE,
            arguments=arguments,
        ).run_id
        print(f"write_pipeline run id is {write_run_id}")
        wait_for_kfp_run_succeeded_from_run_id(kfp_client, write_run_id)

        # Read Pipeline Run
        read_run_id = kfp_client.create_run_from_pipeline_func(
            read_from_volume_pipeline,
            experiment_name=experiment_name,
            namespace=DEFAULT_USER_NAMESPACE,
            arguments=arguments,
        ).run_id
        print(f"read_pipeline run id is {read_run_id}")
        wait_for_kfp_run_succeeded_from_run_id(kfp_client, read_run_id)

        # PVC should now be bound
        claim_entry_after = subprocess.check_output(
            f"kubectl get pvc -n {DEFAULT_USER_NAMESPACE} {CLAIM_NAME} -o=jsonpath='{{.status.phase}}'".split()
        ).decode()
        assert "Bound" in claim_entry_after
