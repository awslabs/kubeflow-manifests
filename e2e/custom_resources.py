"""
Module for helper methods to create and delete kubernetes custom resources (e.g. katib experiments, etc.)
"""

from e2e.utils import unmarshal_yaml

from e2e.constants import KUBEFLOW_GROUP

def create_namespaced_resource_from_yaml(k8s_custom_objects_api_client, yaml_file, group, version, plural, namespace, replacements={}):
    body = unmarshal_yaml(yaml_file, replacements)

    return k8s_custom_objects_api_client.create_namespaced_custom_object(group=group,
                                                                         version=version,
                                                                         namespace=namespace,
                                                                         plural=plural,
                                                                         body=body)

def get_namespaced_resource(k8s_custom_objects_api_client, group, version, plural, namespace, name):
    return k8s_custom_objects_api_client.get_namespaced_custom_object(group=group,
                                                                      version=version,
                                                                      namespace=namespace,
                                                                      plural=plural,
                                                                      name=name)

def delete_namespaced_resource(k8s_custom_objects_api_client, group, version, plural, namespace, name):
    return k8s_custom_objects_api_client.delete_namespaced_custom_object(group=group,
                                                                         version=version,
                                                                         namespace=namespace,
                                                                         plural=plural,
                                                                         name=name)

def create_katib_experiment_from_yaml(k8s_custom_objects_api_client, yaml_file, namespace, replacements={}):
    return create_namespaced_resource_from_yaml(k8s_custom_objects_api_client,
                                                yaml_file,
                                                group=KUBEFLOW_GROUP,
                                                version="v1beta1",
                                                namespace=namespace,
                                                plural="experiments",
                                                replacements=replacements)

def get_katib_experiment(k8s_custom_objects_api_client, namespace, name):
    return get_namespaced_resource(k8s_custom_objects_api_client,
                                    group=KUBEFLOW_GROUP,
                                    version="v1beta1",
                                    namespace=namespace,
                                    plural="experiments",
                                    name=name)
                           
def delete_katib_experiment(k8s_custom_objects_api_client, namespace, name):
    return delete_namespaced_resource(k8s_custom_objects_api_client,
                                    group=KUBEFLOW_GROUP,
                                    version="v1beta1",
                                    namespace=namespace,
                                    plural="experiments",
                                    name=name)