import requests

KUBEFLOW_DOMAIN = "kubeflow.example.com"
PROFILE_NAMESPACE = "staging"
URL = f"https://sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v1/models/sklearn-iris:predict"
HEADERS = {
    "Host": f"sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}",
    "x-api-key": "token1",
}

data = {"instances": [[6.8, 2.8, 4.8, 1.4], [6.0, 3.4, 4.5, 1.6]]}


response = requests.post(URL, headers=HEADERS, json=data)
print("Status Code", response.status_code)
print("JSON Response ", response.json())
