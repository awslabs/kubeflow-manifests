import requests
import os
import json

from e2e.utils.utils import load_json_file

KUBEFLOW_DOMAIN = os.environ.get("KUBEFLOW_DOMAIN", "kubeflow.example.com")
PROFILE_NAMESPACE = os.environ.get("PROFILE_NAMESPACE", "staging")
HTTP_HEADER_NAME = os.environ.get("HTTP_HEADER_NAME", "x-api-key")
HTTP_HEADER_VALUE = os.environ.get("HTTP_HEADER_VALUE", "token1")
MODEL_NAME = os.environ.get("MODEL_NAME", "sklearn-irisv2")

URL = f"https://{MODEL_NAME}.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v2/models/{MODEL_NAME}/infer"
HEADERS = {
    "Host": f"{MODEL_NAME}.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}",
    f"{HTTP_HEADER_NAME}": f"{HTTP_HEADER_VALUE}",
}

data = load_json_file("./utils/kserve/iris-input.json")

response = requests.post(URL, headers=HEADERS, json=data)
print("Status Code", response.status_code)
print("JSON Response ", json.dumps(response.json(), indent=2))
