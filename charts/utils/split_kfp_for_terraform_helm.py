import argparse
import os
import subprocess
import shutil

parser = argparse.ArgumentParser(description='Split KFP helm charts since terraform fails with helm charts of a certain size.')
parser.add_argument('--helm-chart-folder', dest='helm_chart_folder', help='helm chart folder')
parser.add_argument('--overwrite', default=False, help='recreates the folders if they already exist')

args = parser.parse_args()

kfp_chart_path = os.path.abspath(args.helm_chart_folder)
kfp_chart_path_parent = os.path.dirname(kfp_chart_path)
overwrite_folders = args.overwrite

folder_prefix = os.path.basename(kfp_chart_path) + "-part"

split_1_path = os.path.join(kfp_chart_path_parent, f"{folder_prefix}-1")
split_2_path = os.path.join(kfp_chart_path_parent, f"{folder_prefix}-2")

if overwrite_folders:
    shutil.rmtree(split_1_path)
    shutil.rmtree(split_2_path)
elif os.path.exists(split_1_path) or os.path.exists(split_2_path):
    print("Skipping creation, a folder already exists and overwrite is false.")
    raise Exception("Folder(s) already exists")

split_1_desired = ['Role', 'Certificate', 'PriorityClass', 'ClusterRoleBinding', 'ClusterRole', 'RoleBinding', 'MutatingWebhookConfiguration', 'ServiceAccount', 'Secret', 'ConfigMap', 'Service', 'VirtualService', 'Issuer']

split_2_desired = ['CompositeController', 'StatefulSet', 'PersistentVolumeClaim', 'DestinationRule', 'AuthorizationPolicy', 'Deployment']

def keep_folders(path, desired):
    for root, dirs, _ in os.walk(os.path.join(path, "templates")):
        for dir in dirs:
            if dir not in desired:
                shutil.rmtree(os.path.join(root, dir))

shutil.copytree(kfp_chart_path, split_1_path)
shutil.copytree(kfp_chart_path, split_2_path)

keep_folders(split_1_path, split_1_desired)
keep_folders(split_2_path, split_2_desired)