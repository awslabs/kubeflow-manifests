import subprocess
from e2e.utils.utils import load_yaml_file, load_multiple_yaml_files
import pytest
import shutil
import os

KUSTOMIZED_BUILD_OUTPUT_PATH = "helmify/resources/kustomized_output_files"

config_file_path = "./helmify/config.yaml"
cfg = load_yaml_file(file_path=config_file_path)
kustomize_yaml_file_paths = cfg["kustomize_output_yaml_paths"]
helm_yaml_file_paths = cfg["helm_output_yaml_paths"]
chart_names = cfg["helm_chart_names"]
test_data=[]
for i in range (0,len(kustomize_yaml_file_paths)):
    test_data.append([kustomize_yaml_file_paths[i],helm_yaml_file_paths[i],chart_names[i]])


def generate_helm_template(helm_chart_path, helm_chart_name):
    print("creating a copy of existing helm chart folder.")
    shutil.copytree(f"{helm_chart_path}",f"{helm_chart_path}/{helm_chart_name}_copy")
    copy_helm_path = f"{helm_chart_path}/{helm_chart_name}_copy"

    #move crds to template folder
    print("moving crds files to template folder")
    
    if os.path.isdir(f"{copy_helm_path}/crds"):
        for file in os.listdir(f"{copy_helm_path}/crds"):
            source = f"{copy_helm_path}/crds/{file}"
            dest = f"{copy_helm_path}/templates/{file}"
            shutil.move(source,dest)

    helmified_file_name = f"{helm_chart_name}-helmified.yaml"
    os.system(f"helm template {copy_helm_path} > {helmified_file_name}")
    #delete the copy helm folder
    shutil.rmtree(f"{copy_helm_path}")
    print(f"deleted the copy helm folder.")
    #move it to kustomize build
    source = f"{helmified_file_name}"
    dest = f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{helm_chart_name}-helmified.yaml"
    shutil.move(source,dest)
    #finished moving



def find_mirrored_yaml_file(kind,name,file_path):
    helmified_content = load_multiple_yaml_files(file_path=f"{file_path}")
    for data in helmified_content:
        compared_kind = data['kind']
        compared_name = data['metadata']['name']
        if compared_kind == kind and compared_name == name:
            return data
    return None


@pytest.fixture
def kustomize_path():
    return kustomize_yaml_file_paths

@pytest.fixture
def helm_path():
    return helm_yaml_file_paths


@pytest.mark.parametrize("kustomize_path, helm_path, chart_name",test_data)
def test_same_files_length(kustomize_path, helm_path, chart_name):
        generate_helm_template(helm_path,chart_name)

        kustomized_content = load_multiple_yaml_files(file_path=f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{kustomize_path}")
        helmified_content = load_multiple_yaml_files(file_path=f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{chart_name}-helmified.yaml")
        file1_length = len(list(kustomized_content))
        file2_length = len(list(helmified_content))
        assert file1_length == file2_length

@pytest.mark.parametrize("kustomize_path, helm_path, chart_name",test_data)
def test_identical_yaml_files(kustomize_path, helm_path, chart_name):
        kustomized_content = load_multiple_yaml_files(file_path=f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{kustomize_path}")
        
        #find same helm yaml files
        for data in kustomized_content:
            kind = data['kind']
            name = data['metadata']['name']
            compare_data = find_mirrored_yaml_file(kind,name,f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{chart_name}-helmified.yaml")
            if compare_data == None:
                raise Exception(f"No such mirrored yaml file exists for kind = {kind}; name = {name}.")
            assert data == compare_data



