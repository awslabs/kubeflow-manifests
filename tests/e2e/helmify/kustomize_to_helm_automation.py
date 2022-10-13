import logging

import os
import shutil
import unittest
from numpy import character

import yaml
from e2e.utils.utils import print_banner, load_yaml_file, load_multiple_yaml_files, write_yaml_file
from e2e.helmify import common

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KUSTOMIZED_BUILD_OUTPUT_PATH = "../unit-tests/helmify/resources/kustomized_output_files"


def main():
    config_file_path = common.CONFIG_FILE
    print_banner("Reading Config")
    cfg = load_yaml_file(file_path=config_file_path)
    #a list
    kustomized_paths = cfg["Kustomization Filepaths"]
    helm_chart_names = cfg["Helm Chart Names"]
    helm_chart_paths = cfg["Output Helm Filepaths"]
    for i in range (0,len(helm_chart_names)):
        curdir = f"{os.getcwd()}"
        print_banner(f"==========Converting '{helm_chart_names[i]}'==========")
        print("Creating Kustomize Build Yaml File ")
        kustomize_build(kustomized_paths[i], helm_chart_names[i],KUSTOMIZED_BUILD_OUTPUT_PATH, curdir)
        
        print("Splitting Consolidated Kustomize Build Yaml File into Individual Files")
        split_yaml(KUSTOMIZED_BUILD_OUTPUT_PATH, helm_chart_names[i])
        print("Creating Helm Chart Based On Kustomize Build Output")
        create_helm_chart(helm_chart_paths[i], helm_chart_names[i], curdir)
        move_yaml_files_to_helm_template(KUSTOMIZED_BUILD_OUTPUT_PATH,helm_chart_paths[i],helm_chart_names[i])
        find_failed_yaml_files(helm_chart_paths[i], helm_chart_names[i])
        cleanup(KUSTOMIZED_BUILD_OUTPUT_PATH)
        print("Generating Consolidated Helm Manifest")

def kustomize_build(kustomized_path: str, helm_chart_name: str, output_path: str, curdir: str):
    kustomized_file_name = f"{helm_chart_name}-kustomized.yaml"
    command = f"kustomize build {kustomized_path} > {kustomized_file_name}"
    os.system(command)
    logger.info(f"kustomize build completed, file is saved in '{curdir}/{kustomized_file_name}'")
    if not os.path.isfile(f"{curdir}/{helm_chart_name}-kustomized.yaml"):
        raise Exception("kustomized yaml file is not generated.")
    #move to output path
    source=f"{curdir}/{helm_chart_name}-kustomized.yaml"
    dest=f"{output_path}/{helm_chart_name}-kustomized.yaml"
    shutil.move(source,dest)


def split_yaml(kustomized_output_path: str ,helm_chart_name: str):
    kind_set = set()
    kustomized_file_name = f"{helm_chart_name}-kustomized.yaml"
    output_path = f"{kustomized_output_path}/output"
    logger.info(f"creating temporary output folder to store splitted yaml files: '{output_path}'")
    if os.path.isdir(output_path) == False:
        os.mkdir(output_path)
    
    content = load_multiple_yaml_files(file_path=f"{kustomized_output_path}/{kustomized_file_name}")
    for data in content:
        kind = data['kind'] 
        if kind not in kind_set:
            kind_set.add(kind)
            if os.path.isdir(f"{kustomized_output_path}/output/{kind}") == False:
                os.mkdir(f"{kustomized_output_path}/output/{kind}")
        if 'namespace' in data['metadata']:
            namespace = data['metadata']['namespace']
            name = data['metadata']['name']
            output_file_name = f"{name}-{namespace}-{kind}"
        else:
            name = data['metadata']['name']
            output_file_name = f"{name}-{kind}"

        #write file into outputFile
        write_yaml_file(yaml_content=data, file_path=f"{kustomized_output_path}/{output_file_name}.yaml")

        #move file to folder
        source = f"{kustomized_output_path}/{output_file_name}.yaml"
        dest = f"{kustomized_output_path}/output/{kind}/{output_file_name}.yaml"
        shutil.move(source,dest)

    logger.info(f"finished splitting!")
                    

def create_helm_chart(helm_chart_path: str, helm_chart_name: str, curdir: str):
    print(helm_chart_path)
    if os.path.isdir(f"{helm_chart_path}") == False:
        os.mkdir(f"{helm_chart_path}")
    os.chdir(f"{helm_chart_path}")
    if os.path.isdir(f"{helm_chart_name}"):
        os.chdir(curdir)
        return

    os.system(f"helm create {helm_chart_name}")
    if not os.path.isdir(f"{helm_chart_name}"):
        raise Exception ("helm chart was not created successfully.")

    #cleaning up template folder
    logger.info(f"cleaning up redundant default helm files.")
    dir = f"{helm_chart_name}/templates"
    shutil.rmtree(f"{dir}/tests")
    #delete all autogenerate yaml folders
    filelist = [ f for f in os.listdir(dir) if f.endswith(".yaml") ]
    for f in filelist:
        os.remove(os.path.join(dir, f))
    #delete NOTES.txt
    os.remove(f"{dir}/NOTES.txt")

    logger.info(f"empty out value.yaml file.")
    #empty values.yaml
    value_file = f"{helm_chart_name}/values.yaml"
    empty_yaml_file = None
    write_yaml_file(yaml_content=empty_yaml_file, file_path=value_file)
    os.chdir(curdir)

def move_yaml_files_to_helm_template(kustomized_output_path: str, helm_chart_path: str, helm_chart_name: str):
    output_path = f"{kustomized_output_path}/output"
    helm_dir = f"{helm_chart_path}/{helm_chart_name}"
    #move crds
    if os.path.isdir(f"{helm_dir}/crds") == False:
        os.mkdir(f"{helm_dir}/crds")
        logger.info(f"created crds folder inside helm chart for Custom Resource Definition yaml files.")
    if os.path.isdir(f"{output_path}/CustomResourceDefinition"):
        logger.info(f"moving Custom Resource Definition yaml files into crds folder.")
        filelist = [ file for file in os.listdir(f"{output_path}/CustomResourceDefinition")]
        crd_dest_path = f"{helm_dir}/crds"
        for file in filelist:
            shutil.move(f"{output_path}/CustomResourceDefinition/{file}",f"{crd_dest_path}/{file}")
    
    logger.info(f"completed moving Custom Resource Definition yaml files into crds folder.")
    #move rest of kinds
    obj = os.scandir(output_path)
    logger.info(f"moving the rest of the kinds yaml files into helm templates folder.")
    for entry in obj :
        if entry.is_dir() or entry.is_file():
            #move files to template
            if (entry.name != 'CustomResourceDefinition'):
                if os.path.isdir(f"{helm_dir}/templates/{entry.name}") == False:
                    os.mkdir(f"{helm_dir}/templates/{entry.name}")
                filelist = [ file for file in os.listdir(f"{output_path}/{entry.name}") if file.endswith(".yaml") ]
                for file in filelist:
                    source = f"{output_path}/{entry.name}/{file}"
                    dest = f"{helm_dir}/templates/{entry.name}/{file}"
                    shutil.move(source,dest)
    logger.info(f"completed moving the rest of the kinds yaml files into helm templates folder.")

def find_failed_yaml_files (helm_chart_path: str, helm_chart_name: str):
    dir = f"{helm_chart_path}/{helm_chart_name}"
    problem_filelist = []
    
    file_types=["ConfigMap","ClusterServingRuntime"]
    for file_type in file_types:
        if os.path.isdir(f"{dir}/templates/{file_type}"):
            logger.info(f"finding potential problematic yaml files in {file_type} folder.")
            filelist = [ f for f in os.listdir(f"{dir}/templates/{file_type}")]
            for f in filelist:
                content = load_multiple_yaml_files(file_path=f"{dir}/templates/{file_type}/{f}") 
                for elem in content:
                    find_failed_files_recursive_lookup(elem,problem_filelist,f)
                            
            
            if problem_filelist:
                if os.path.isdir(f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions") == False:
                    os.mkdir(f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions")
                logger.info(f"Some Yaml files in {file_type} folder are conflicted with helm template formatting. Please check on files inside failed_helm_conversions folder. Replace all backticks with double quotes, then all {{ with {{`{{ and all }} with }}`}}")
                for file in problem_filelist:
                    source = f"{helm_chart_path}/{helm_chart_name}/templates/{file_type}/{file}"
                    dest = f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions/{file}"
                    shutil.move(source,dest)




def find_failed_files_recursive_lookup(dictionaries: dict, problem_filelist: list, file: yaml):
    for k, v in dictionaries.items():
        if isinstance(v, dict):
            find_failed_files_recursive_lookup(v, problem_filelist, file)
            
        else:
            flag = search(v,'{{') or search(v,'}}')
            if flag:
                problem_filelist.append(file)
                return
                   
def search(value: str, search_for: character):
    n = len(value)
    for i in range(0, n-1):
        if search_for[0] == value[i] and search_for[1] == value[i+1]:
            return True
    return False


def cleanup(kustomized_build_output: str):
    logger.info(f"deleting temporary output folder: {kustomized_build_output}/output")
    shutil.rmtree(f"{kustomized_build_output}/output")
    logger.info("folder deleted.")



if __name__ == "__main__":
    main()