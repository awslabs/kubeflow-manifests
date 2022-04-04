import subprocess
import time
import boto3
import os
import json

import pytest
import boto3

from e2e.fixtures.cluster import cluster
from e2e.conftest import region
from e2e.utils.config import metadata


import requests
import pytest

from e2e.utils.config import metadata, configure_env_file
from e2e.conftest import region

from e2e.fixtures.cluster import cluster
from e2e.fixtures.kustomize import kustomize, clone_upstream
from e2e.fixtures.clients import account_id

from e2e.fixtures.cognito_dependencies import (
    cognito_bootstrap,
)
from e2e.utils.config import configure_resource_fixture

from e2e.utils.utils import wait_for



@pytest.fixture(scope="class")
def cloudwatch_bootstrap(metadata, region, request, cluster):

    cognito_deps = {"cluster": {"region": region, "name": cluster}}

    def on_create():
        return

    def on_delete():
        return

    return configure_resource_fixture(
        metadata, request, cognito_deps, "cognito_dependencies", on_create, on_delete
    )


def wait_for_cloudwatch_logs(cloudwatch, ClusterName):
    def wait(period_length=10, periods=10):
        for _ in range(periods):
            fluent_bit_log_groups = cloudwatch.describe_log_groups(
                logGroupNamePrefix=f"/aws/containerinsights/{ClusterName}"
            )
            if len(fluent_bit_log_groups["logGroups"]) != 0:
                return True
            time.sleep(period_length)
        return False

    return wait()


class TestCognito:
    @pytest.fixture(scope="class")
    def setup(self, metadata):
        metadata_file = metadata.to_file()
        metadata.log()
        print("Created metadata file for TestSanity", metadata_file)

    def test_url_is_up(self, setup, region, cloudwatch_bootstrap, metadata):
        ClusterName = metadata.get("cluster_name")
        client = boto3.client("eks", region_name=region)
        nodegroup = client.list_nodegroups(clusterName=ClusterName)["nodegroups"]
        a = client.describe_nodegroup(
            clusterName=ClusterName, nodegroupName=nodegroup[0]
        )
        nodeRole = (a["nodegroup"]["nodeRole"]).split("/")[1]
        iam_client = boto3.client("iam", region_name=region)
        iam_client.attach_role_policy(
            RoleName=nodeRole,
            PolicyArn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
        )
        LogRegion = region
        FluentBitHttpPort = "2020"
        FluentBitReadFromHead = "Off"
        FluentBitHttpServer = "On"
        FluentBitReadFromTail = "On"
        cmd = []
        cmd += "kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/cloudwatch-namespace.yaml".split()
        subprocess.call(cmd)
        cmd = []
        cmd += f"kubectl create configmap fluent-bit-cluster-info \
--from-literal=cluster.name={ClusterName} \
--from-literal=http.server={FluentBitHttpServer} \
--from-literal=http.port={FluentBitHttpPort} \
--from-literal=read.head={FluentBitReadFromHead} \
--from-literal=read.tail={FluentBitReadFromTail} \
--from-literal=logs.region={LogRegion} -n amazon-cloudwatch".split()
        subprocess.call(cmd)

        cmd = []
        cmd += "kubectl apply -f https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/fluent-bit/fluent-bit.yaml".split()
        subprocess.call(cmd)
        cloudwatch = boto3.client("logs", region_name=region)
        assert wait_for_cloudwatch_logs(cloudwatch, ClusterName)
        cmd = []
        cmd += "kubectl delete namespace amazon-cloudwatch".split()
        subprocess.call(cmd)
        for group in cloudwatch.describe_log_groups(
            logGroupNamePrefix=f"/aws/containerinsights/{ClusterName}"
        )["logGroups"]:
            cloudwatch.delete_log_group(logGroupName=group["logGroupName"])
