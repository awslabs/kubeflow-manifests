from e2e.utils.utils import load_yaml_file, load_multiple_yaml_files
import pytest


config_file_path = "./helmify/config.yaml"
cfg = load_yaml_file(file_path=config_file_path)
kustomize_yaml_file_path = cfg["Kustomize output yaml path"]
helm_yaml_file_path = cfg["Helm output yaml path"]



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
    return kustomize_yaml_file_path

@pytest.fixture
def helm_path():
    return helm_yaml_file_path

def test_same_files_length(kustomize_path, helm_path):

        kustomized_content = load_multiple_yaml_files(file_path=f"{kustomize_path}")
        helmified_content = load_multiple_yaml_files(file_path=f"{helm_path}")
        file1_length = len(list(kustomized_content))
        file2_length = len(list(helmified_content))
        assert file1_length == file2_length

def test_identical_yaml_files(kustomize_path, helm_path):
        kustomized_content = load_multiple_yaml_files(file_path=f"{kustomize_path}")
        
        #find same helm yaml files
        for data in kustomized_content:
            kind = data['kind']
            name = data['metadata']['name']
            compare_data = find_mirrored_yaml_file(kind,name,helm_path)
            if compare_data == None:
                raise Exception(f"No such mirrored yaml file exists for kind = {kind}; name = {name}.")
            assert data == compare_data



