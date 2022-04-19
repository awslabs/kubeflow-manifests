import requests
import os

KUBEFLOW_DOMAIN = os.environ.get("KUBEFLOW_DOMAIN", "kubeflow.example.com")
PROFILE_NAMESPACE = os.environ.get("PROFILE_NAMESPACE", "staging")
USERNAME = os.environ.get("USERNAME", "user@example.com")
PASSWORD = os.environ.get("PASSWORD", "12341234")

URL = f"https://sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}/v1/models/sklearn-iris:predict"
HEADERS = {"Host": f"sklearn-iris.{PROFILE_NAMESPACE}.{KUBEFLOW_DOMAIN}"}
DASHBOARD_URL = f"https://kubeflow.{KUBEFLOW_DOMAIN}"

data = {"instances": [[6.8, 2.8, 4.8, 1.4], [6.0, 3.4, 4.5, 1.6]]}


def session_cookie(host, login, password):
    session = requests.Session()
    response = session.get(host)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"login": login, "password": password}
    session.post(response.url, headers=headers, data=data)
    session_cookie = session.cookies.get_dict()["authservice_session"]
    return session_cookie


cookie = {"authservice_session": session_cookie(DASHBOARD_URL, USERNAME, PASSWORD)}

response = requests.post(URL, headers=HEADERS, json=data, cookies=cookie)
print("Status Code", response.status_code)
print("JSON Response ", response.json())
