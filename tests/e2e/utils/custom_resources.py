"""
Module for helper methods to create and delete kubernetes custom resources (e.g. katib experiments, etc.)
"""

from e2e.utils.utils import unmarshal_yaml
from e2e.fixtures.clients import create_k8s_custom_objects_api_client

from e2e.utils.constants import KUBEFLOW_GROUP


def create_namespaced_resource_from_yaml(
    cluster, region, yaml_file, group, version, plural, namespace, replacements={}
):
    body = unmarshal_yaml(yaml_file, replacements)
    client = create_k8s_custom_objects_api_client(cluster, region)

    return client.create_namespaced_custom_object(
        group=group, version=version, namespace=namespace, plural=plural, body=body
    )


def get_namespaced_resource(cluster, region, group, version, plural, namespace, name):
    client = create_k8s_custom_objects_api_client(cluster, region)

    return client.get_namespaced_custom_object(
        group=group, version=version, namespace=namespace, plural=plural, name=name
    )


def delete_namespaced_resource(
    cluster, region, group, version, plural, namespace, name
):
    client = create_k8s_custom_objects_api_client(cluster, region)
    return client.delete_namespaced_custom_object(
        group=group, version=version, namespace=namespace, plural=plural, name=name
    )


def create_katib_experiment_from_yaml(
    cluster, region, yaml_file, namespace, replacements={}
):
    return create_namespaced_resource_from_yaml(
        cluster,
        region,
        yaml_file,
        group=KUBEFLOW_GROUP,
        version="v1beta1",
        namespace=namespace,
        plural="experiments",
        replacements=replacements,
    )


def get_katib_experiment(cluster, region, namespace, name):
    return get_namespaced_resource(
        cluster,
        region,
        group=KUBEFLOW_GROUP,
        version="v1beta1",
        namespace=namespace,
        plural="experiments",
        name=name,
    )


def delete_katib_experiment(cluster, region, namespace, name):
    return delete_namespaced_resource(
        cluster,
        region,
        group=KUBEFLOW_GROUP,
        version="v1beta1",
        namespace=namespace,
        plural="experiments",
        name=name,
    )


def get_ingress(cluster, region, name="istio-ingress", namespace="istio-system"):
    return get_namespaced_resource(
        cluster,
        region,
        group="networking.k8s.io",
        version="v1beta1",
        namespace=namespace,
        plural="ingresses",
        name=name,
    )
