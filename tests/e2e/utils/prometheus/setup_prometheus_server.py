import subprocess
import time
import os
import boto3
import tempfile
from e2e.utils.prometheus.createPolicy_AMPIngest import *
from e2e.utils.utils import wait_for
from e2e.fixtures.cluster import associate_iam_oidc_provider

prometheus_yaml_files_directory = "../../deployments/add-ons/prometheus"

def replace_params_env_in_line(file_path, original_to_replacement_dict):
    updated_file_contents = ""
    with open(file_path, 'r') as original_file:
        for line in original_file:
            for key in original_to_replacement_dict:
                if key == line.split("=")[0]:
                    line = f'{key}={original_to_replacement_dict.get(key)}\n'
            updated_file_contents += line
    with open(file_path, 'w') as updated_file:
        updated_file.write(updated_file_contents)

def update_params_env(workspace_id, region, params_env_file_path):
    original_to_replacement_dict = {}
    original_to_replacement_dict['workspaceId'] = workspace_id
    original_to_replacement_dict['workspaceRegion'] = region
    replace_params_env_in_line(params_env_file_path, original_to_replacement_dict)

def create_AMP_workspace(region):
    amp_client = boto3.client('amp', region_name=region)
    
    workspace_id = amp_client.create_workspace(alias = 'test_AMP_workspace')['workspaceId']
    print(f"Created Workspace ID: {workspace_id}")

    def check_active_workspace_status():
        workspace_status = amp_client.describe_workspace(workspaceId=workspace_id).get("workspace").get("status").get("statusCode")
        print(f"Workspace Status: {workspace_status}")
        assert "ACTIVE" == workspace_status
    
    wait_for(check_active_workspace_status)
    
    return workspace_id

def set_up_prometheus_for_AMP(cluster_name, region):    
    associate_iam_oidc_provider(cluster_name, region)

    policy_arn = create_AMP_ingest_policy()
    
    # Create AMP service account:
    create_AMP_service_account_command = f'eksctl create iamserviceaccount --name {SERVICE_ACCOUNT_AMP_INGEST_NAME} --role-name {SERVICE_ACCOUNT_IAM_AMP_INGEST_ROLE} --namespace {PROMETHEUS_NAMESPACE} --cluster {cluster_name} --attach-policy-arn {policy_arn} --override-existing-serviceaccounts --approve --region {region}'.split()
    subprocess.call(create_AMP_service_account_command, encoding="utf-8")

    workspace_id = create_AMP_workspace(region)
    
    # Edit params.env to use workspace-id and region
    update_params_env(workspace_id, region, f'{prometheus_yaml_files_directory}/params.env')
    
    create_namespace_command = f'kubectl create namespace {PROMETHEUS_NAMESPACE}'.split()
    subprocess.call(create_namespace_command)
    
    kustomize_build_command = f'kustomize build {prometheus_yaml_files_directory}'.split()
    print("About to run kustomize command.")
    kustomize_build_output = subprocess.check_output(kustomize_build_command)
    print("Finished running kustomize command.")
    
    print("About apply kustomize output.")
    with tempfile.NamedTemporaryFile() as tmp_file:
        tmp_file.write(kustomize_build_output)
        tmp_file.flush()
        kubectl_apply_command = f'kubectl apply -f {tmp_file.name}'.split()
        subprocess.call(kubectl_apply_command, encoding="utf-8")
    print("Finished applying kustomize output.")

    return workspace_id

def set_up_prometheus_port_forwarding():
    print("Entered prometheus port_forwarding_function.")
    def get_prometheus_pod_name():
        get_pod_name_command = f'kubectl get pods --namespace={PROMETHEUS_NAMESPACE}'.split()
        print(' '.join(get_pod_name_command))
        pod_list = subprocess.check_output(get_pod_name_command, encoding="utf-8").split('\n')[1:]
        print(f"{PROMETHEUS_NAMESPACE} Pods list: {pod_list}")
        assert 0 < len(pod_list)
        prometheus_pod_name = None
        for pod in pod_list:
            pod_name = pod.split()[0]
            print("pod name and status:", pod)
            pod_name_array = pod_name.split('-')
            if (('p' == pod_name[0])
                and ('prometheus' == pod_name_array[0])
                and ('deployment' == pod_name_array[1])):
                describe_pod_command = f'kubectl describe pod {pod_name} --namespace {PROMETHEUS_NAMESPACE}'.split()
                print('\n\nAbout to call describe pod command!\n\n')
                print(subprocess.check_output(describe_pod_command, encoding="utf-8"))
                print('\n\nDescribe Finished\n\n')
#                get_ns_pod_logs_command = f'kubectl logs {pod_name} --namespace {PROMETHEUS_NAMESPACE}'.split()
#                print(f"\n\nAbout to get {PROMETHEUS_NAMESPACE}/{pod_name} logs!\n\n")
#                print(subprocess.check_output(get_ns_pod_logs_command, encoding="utf-8"))
#                print('\n\nLogs Finished\n\n')
                pod_status = pod.split()[1]
                print("pod_status:", pod_status)
                assert "1/1" == pod_status
                print("Assert running was succesfull.")
                prometheus_pod_name = pod_name
                break
        return prometheus_pod_name

    prometheus_pod_name = wait_for(get_prometheus_pod_name, timeout=90, interval=30)
    if None == prometheus_pod_name:
        raise ValueError("Prometheus Pod Not Running.")

    set_up_port_forwarding_command = f'kubectl port-forward {prometheus_pod_name} 9090:9090 -n {PROMETHEUS_NAMESPACE}'.split()
    print(" ".join(set_up_port_forwarding_command))
    port_forwarding_process = subprocess.Popen(set_up_port_forwarding_command)
    time.sleep(10)  # Wait 10 seconds for port forwarding to open
    return port_forwarding_process
    
def check_prometheus_is_running():
    check_up_command = 'curl http://localhost:9090/api/v1/query?query=up'.split()
    print(' '.join(check_up_command))
    up_results = subprocess.check_output(check_up_command, encoding="utf-8")
    assert True==bool(up_results)

def get_kfp_create_experiment_count(prometheus_query='experiment_server_create_requests'):
    prometheus_curl_command = f"curl http://localhost:9090/api/v1/query?query={prometheus_query}".split()
    print(f"Prometheus curl command:\n{' '.join(prometheus_curl_command)}")
    print(f"Broken up prometheus curl command:\n{prometheus_curl_command}")
    prometheus_query_results = subprocess.check_output(prometheus_curl_command, encoding="utf-8")
    print(f"Prometheus query results:\n{prometheus_query_results}")
    prometheus_create_experiment_count = prometheus_query_results.split(",")[-1].split('"')[1]
    print("prometheus_create_experiment_count:", prometheus_create_experiment_count)
    return prometheus_create_experiment_count
    
def check_AMP_connects_to_prometheus(region, workspace_id, expected_value, prometheus_query='experiment_server_create_requests', AMP_query='experiment_server_create_requests', katib_query=False):
    
    time.sleep(60) # Wait for prometheus to scrape.
    access_key = os.environ['AWS_ACCESS_KEY_ID']
    secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

    print(f"Using Workspace ID: {workspace_id}")
    
    AMP_awscurl_command = f'awscurl --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query?query={AMP_query}'.split()
#    AMP_awscurl_command = f'awscurl --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query -d "query={AMP_query}" --data-binary'.split()
#    AMP_awscurl_command = f'awscurl -v --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query -d query=rest_client_requests_total -d code=403 -d host=10.100.0.1:443 -d method=GET'.split()
#    AMP_awscurl_command = (f'awscurl -v --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query -d ' + '{"query":"rest_client_requests_total","code":"403","host":"10.100.0.1:443","method":"GET"}').split()
#    AMP_awscurl_command = f'awscurl --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query -d "query={AMP_query}"'.split()

    print(f'AMP awscurl command:\n{" ".join(AMP_awscurl_command)}')
    print(f'Broken up AMP awscurl command:\n{AMP_awscurl_command}')
    AMP_query_results = subprocess.check_output(AMP_awscurl_command, encoding="utf-8")

    if katib_query:
        broad_dict = json.loads(AMP_query_results)
        for specific_dict in broad_dict["data"]["result"]:
            if  (specific_dict["metric"]["code"] == "403") and (specific_dict["metric"]["job"] == "katib-controller"):
                AMP_query_results=json.dumps(specific_dict)
                break
    
    print(f"AMP_query_results:\n{AMP_query_results}")
    AMP_create_experiment_count = AMP_query_results.split(",")[-1].split('"')[1]
    print("AMP_create_experiment_count:", AMP_create_experiment_count)

    prometheus_create_experiment_count = get_kfp_create_experiment_count(prometheus_query)
    
    print(f"Asserting AMP == prometheus: {AMP_create_experiment_count} == {prometheus_create_experiment_count}")
    assert AMP_create_experiment_count == prometheus_create_experiment_count
    print(f"Asserting expected == prometheus: {expected_value} == {prometheus_create_experiment_count}")
    assert str(expected_value) == prometheus_create_experiment_count
    return AMP_create_experiment_count

def delete_AMP_resources(cluster_name, region, workspace_id):
    print("About to delete service account and role.")
    delete_AMP_service_account_command = f'eksctl delete iamserviceaccount --name amp-iamproxy-ingest-service-account --namespace {PROMETHEUS_NAMESPACE} --cluster {cluster_name} --region {region}'.split()
    subprocess.call(delete_AMP_service_account_command, encoding="utf-8")
    print("Finished deleting service account and role.")

    wait_for(delete_policy)
    
    amp_client = boto3.client('amp', region_name=region)

    print("About to delete workspace.")
    amp_client.delete_workspace(workspaceId=workspace_id)

    time.sleep(10) # Wait for the workspace to delete.
    
    try:
        amp_client.describe_workspace(workspaceId=workspace_id)
    except Exception as e:
        print(e)
        print("Finished deleting workspace.")
        return
    raise AssertionError("The workspace with id", workspace_id, "is in the {workspace_status} state.")
