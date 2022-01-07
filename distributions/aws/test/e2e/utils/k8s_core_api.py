"""
Module for helper methods to create and delete kubernetes core api resources (e.g. pods, namespaces, etc.)
"""

from kubernetes.client import V1Namespace
from kubernetes.client.exceptions import ApiException

from e2e.fixtures.clients import create_k8s_core_api_client


def create_namespace(cluster, region, namespace_name):
    client = create_k8s_core_api_client(cluster, region)
    try:
        client.create_namespace(V1Namespace(metadata=dict(name=namespace_name)))
    except ApiException as e:
        if "Conflict" != e.reason:
            raise e
