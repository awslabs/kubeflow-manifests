import requests
import os

KUBEFLOW_DOMAIN = os.environ.get("KUBEFLOW_DOMAIN", "kubeflow.example.com")
PROFILE_NAMESPACE = os.environ.get("PROFILE_NAMESPACE", "staging")
HTTP_HEADER_NAME = os.environ.get("HTTP_HEADER_NAME", "x-api-key")
HTTP_HEADER_VALUE = os.environ.get("HTTP_HEADER_VALUE", "token1")

URL = f"https://sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v1/models/sklearn-iris:predict"
HEADERS = {
    "Host": f"sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}",
    f"{HTTP_HEADER_NAME}": f"{HTTP_HEADER_VALUE}",
}

data = {"instances": [[6.8, 2.8, 4.8, 1.4], [6.0, 3.4, 4.5, 1.6]]}


response = requests.post(URL, headers=HEADERS, json=data)
print("Status Code", response.status_code)
print("JSON Response ", response.json())
