import subprocess
import time
import requests

import pytest

from kubernetes import client, config
import kfp

def client_from_config(cluster, region):
    context = f"Administrator@{cluster}.{region}.eksctl.io"
    return config.new_client_from_config(context=context)

@pytest.fixture(scope="class")
def k8s_core_api_client(cluster, region):
    return client.CoreV1Api(api_client=client_from_config(cluster, region))

@pytest.fixture(scope="class")
def k8s_custom_objects_api_client(cluster, region):
    return client.CustomObjectsApi(api_client=client_from_config(cluster, region))

# todo make port random
@pytest.fixture(scope="class")
def port_forward(kustomize):
    cmd = "kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80".split()
    proc = subprocess.Popen(cmd)
    time.sleep(10)  # Wait 10 seconds for port forwarding to open
    yield
    proc.terminate()

HOST = "http://localhost:8080/"
USERNAME = "user@example.com"
PASSWORD = "12341234"
NAMESPACE = "kubeflow-user-example-com"

@pytest.fixture(scope="class")
def kfp_client(port_forward):
    session = requests.Session()
    response = session.get(HOST)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"login": USERNAME, "password": PASSWORD}
    session.post(response.url, headers=headers, data=data)
    session_cookie = session.cookies.get_dict()["authservice_session"]
    client = kfp.Client(
        host=f"{HOST}/pipeline",
        cookies=f"authservice_session={session_cookie}",
        namespace=NAMESPACE,
    )
    client._context_setting['namespace'] = NAMESPACE    # needs to be set for list_experiments

    return client