import subprocess
import time
import os
import boto3
from e2e.utils.prometheus.createIRSA_AMPIngest import setup_ingest_role, delete_ingest_role
from e2e.utils.prometheus.IAMRolesUtils import get_AWS_account_ID
from e2e.utils.utils import wait_for

def make_new_file_with_replacement(file_path, original_to_replacement_dict):
    new_file_contents = ""
    with open(file_path, 'r') as original_file:
        for original_line in original_file:
            new_line = original_line
            for key in original_to_replacement_dict:
                new_line = new_line.replace(key, original_to_replacement_dict.get(key))
            new_file_contents += new_line
    old_path_array = file_path.split('/')
    print("old_path_array:", old_path_array)
    old_path_array[-1] = 'new-' + old_path_array[-1]
    print("new path array:", old_path_array)
    new_file_path = '/'.join(old_path_array)
    with open(new_file_path, 'w') as new_file:
        new_file.write(new_file_contents)
    return new_file_path

def update_AMP_service_account_id(AMP_service_account_file_path):
    aws_account_id = get_AWS_account_ID()
    original_to_replacement_dict = {}
    original_to_replacement_dict['<my-account-id>'] = aws_account_id
    return make_new_file_with_replacement(AMP_service_account_file_path, original_to_replacement_dict)
    
def update_config_map_AMP_workspace(workspace_id, region, config_map_file_path):
    original_to_replacement_dict = {}
    original_to_replacement_dict['<my-workspace-id>'] = workspace_id
    original_to_replacement_dict['<my-workspace-region>'] = region
    return make_new_file_with_replacement(config_map_file_path, original_to_replacement_dict)

def set_up_prometheus_for_AMP(cluster_name, region):
    amp_client = boto3.client('amp', region_name=region)
    
    create_namespace_command = 'kubectl create namespace monitoring'.split()
    subprocess.call(create_namespace_command)

    workspace_id = amp_client.create_workspace(alias = 'test_AMP_workspace')['workspaceId']
    
    setup_ingest_role(cluster_name, region)

    # Edit AMP service account to use account-id
    new_AMP_service_account = update_AMP_service_account_id('utils/prometheus/AMP-service-account.yaml')
    
    create_AMP_service_account_command = f'kubectl create -f {new_AMP_service_account}'.split()
    subprocess.call(create_AMP_service_account_command, encoding="utf-8")

    create_cluster_role_command = 'kubectl create -f utils/prometheus/clusterRole.yaml'.split()
    subprocess.call(create_cluster_role_command, encoding="utf-8")

    # Edit config map to use workspace-id and region
    new_config_map = update_config_map_AMP_workspace(workspace_id, region, 'utils/prometheus/config-map.yaml')
    
    create_config_map_command = f'kubectl create -f {new_config_map}'.split()
    subprocess.call(create_config_map_command, encoding="utf-8")

    create_prometheus_deployment_command = 'kubectl create -f utils/prometheus/prometheus-deployment.yaml'.split()
    subprocess.call(create_prometheus_deployment_command, encoding="utf-8")

    create_prometheus_server_command = 'kubectl create -f utils/prometheus/prometheus-service.yaml'.split()
    subprocess.call(create_prometheus_server_command, encoding="utf-8")

    return workspace_id

def set_up_prometheus_port_forwarding():
    def callback():
        get_pod_name_command = 'kubectl get pods --namespace=monitoring'.split()
        pod_list = subprocess.check_output(get_pod_name_command, encoding="utf-8").split('\n')[1:]
        prometheus_pod_name = None
        for pod in pod_list:
            pod_name = pod.split()[0]
            print("pod name and status:", pod)
            pod_name_array = pod_name.split('-')
            if (('p' == pod_name[0])
                and ('prometheus' == pod_name_array[0])
                and ('deployment' == pod_name_array[1])):
                print("Made it into inner if loop.")
                describe_pod_command = f'kubectl describe pod {pod_name} --namespace monitoring'.split()
                print('\n\nAbout to call describe pod command!\n\n')
                print(subprocess.check_output(describe_pod_command, encoding="utf-8"))
                print('\n\nDescribe Finished\n\n')
                get_ns_pod_logs_command = f'kubectl logs {pod_name} --namespace monitoring'.split()
                print("\n\nAbout to get monitoring namespace logs!\n\n")
                print(subprocess.check_output(get_ns_pod_logs_command, encoding="utf-8"))
                print('\n\nLogs Finished\n\n')
                pod_status = pod.split()[1]
                print("pod_status:", pod_status)
                assert "1/1" == pod_status
                print("Assert running was succesfull.")
                prometheus_pod_name = pod_name
                break
        return prometheus_pod_name
    
    prometheus_pod_name = wait_for(callback)
    if None == prometheus_pod_name:
        raise ValueError("Prometheus Pod Not Running.")
    print("About to assemble port-forwarding command.")
    set_up_port_forwarding_command = f'kubectl port-forward {prometheus_pod_name} 9090:9090 -n monitoring'.split()
    print("prometheus_pod_name:", prometheus_pod_name)
    print(" ".join(set_up_port_forwarding_command))
    subprocess.Popen(set_up_port_forwarding_command)
    time.sleep(10)  # Wait 10 seconds for port forwarding to open
    
def check_prometheus_is_running():
    check_up_command = 'curl http://localhost:9090/api/v1/query?query=up'.split()
    print(' '.join(check_up_command))
    up_results = subprocess.check_output(check_up_command, encoding="utf-8")
    assert True==bool(up_results)

def check_AMP_connects_to_prometheus(region, workspace_id):
    time.sleep(30) # Wait for promehtue sto scrape.
    access_key = os.environ['AWS_ACCESS_KEY_ID']
    print("ACCESS_KEY:", access_key)
    secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
    print("SECRET_KEY:", secret_key)
    
    AMP_awscurl_command = f'awscurl --access_key {access_key} --secret_key {secret_key} --region {region} --service aps https://aps-workspaces.{region}.amazonaws.com/workspaces/{workspace_id}/api/v1/query?query=experiment_server_create_requests'.split()
    AMP_query_results = subprocess.check_output(AMP_awscurl_command, encoding="utf-8")
    print("AMP_query_results:", AMP_query_results)
    AMP_experiment_count = AMP_query_results.split(",")[-1].split('"')[1]
    print("AMP_experiment_count:", AMP_experiment_count)
    prometheus_curl_command = "curl http://localhost:9090/api/v1/query?query=experiment_server_create_requests".split()
    prometheus_query_results = subprocess.check_output(prometheus_curl_command, encoding="utf-8")
    print("prometheus_query_results:", prometheus_query_results)
    prometheus_experiment_count = prometheus_query_results.split(",")[-1].split('"')[1]
    print("prometheus_experiment_count:", prometheus_experiment_count)
    assert AMP_experiment_count == prometheus_experiment_count
    return AMP_experiment_count

def delete_AMP_resources(region, workspace_id):
    print("About to delete ingest role.")
    delete_ingest_role()
    print("Finished deleting ingest role.")

    print("About to make boto3 amp client.")
    amp_client = boto3.client('amp', region_name=region)

    print("About to delete workspace.")
    amp_client.delete_workspace(workspaceId=workspace_id)
    
    print("About to describe workspace.")
    try:
        amp_client.describe_workspace(workspaceId=workspace_id)
    except Exception as e:
        print(e)
