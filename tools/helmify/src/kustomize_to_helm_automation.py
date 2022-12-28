import logging

import os
import shutil
import unittest
from numpy import character

import yaml
from tests.e2e.utils.utils import (
    print_banner,
    load_yaml_file,
    load_multiple_yaml_files,
    write_yaml_file,
    exec_shell,
)
from tools.helmify.src import common


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KUSTOMIZED_BUILD_OUTPUT_PATH = (
    "./tools/helmify/generated_output/kustomized_output_files"
)
HELM_TEMP_OUTPUT_PATH = "./tools/helmify/generated_output/helm_chart_temp_output_files"
ROOT_DIR = f"{os.getcwd()}"
POSSIBLE_DEPLOYMENT_OPTIONS = [
    "vanilla",
    "cognito",
    "rds-s3",
    "rds-only",
    "s3-only",
    "katib-external-db-with-kubeflow",
]
POSSIBLE_PROBLEM_FILE_TYPES = ["ConfigMap", "ClusterServingRuntime"]


Components = [
    "istio-1-14",
    "dex",
    "oidc-authservice",
    "cluster-local-gateway",
    "kubeflow-namespace",
    "kubeflow-istio-resources",
    "kubeflow-roles",
    "kubeflow-issuer",
    "knative-serving",
    "knative-eventing",
    "kserve",
    "models-web-app",
    "central-dashboard",
    "aws-secrets-manager",
    "kubeflow-pipelines",
    "admission-webhook",
    "jupyter-web-app",
    "notebook-controller",
    "volumes-web-app",
    "training-operator",
    "katib",
    "tensorboards-web-app",
    "tensorboard-controller",
    "profiles-and-kfam",
    "user-namespace",
    "ingress",
    "aws-authservice",
    "aws-telemetry",
]


def kustomize_build(
    kustomized_paths: list, helm_chart_name: str, kustomized_output_files_dir: str
):
    kustomized_file_list = []

    if os.path.isdir(kustomized_output_files_dir) == False:
        exec_shell(f"mkdir -p {kustomized_output_files_dir}")
    for i in range(len(kustomized_paths)):
        kustomized_path = kustomized_paths[i]
        kustomized_file_name = f"{helm_chart_name}-kustomized-{i}.yaml"
        exec_shell(
            f"kustomize build {kustomized_path} > {kustomized_output_files_dir}/{kustomized_file_name}"
        )
        logger.info(
            f"kustomize build completed, file is saved in '{kustomized_output_files_dir}/{kustomized_file_name}'"
        )
        if not os.path.isfile(f"{kustomized_output_files_dir}/{kustomized_file_name}"):
            raise Exception("kustomized yaml file is not generated.")
        kustomized_file_list.append(kustomized_file_name)
    return kustomized_file_list


def split_yaml(
    kustomized_file_list: list,
    splitted_output_path: str,
    kustomized_output_files_dir: str,
):
    if os.path.isdir(splitted_output_path) == False:
        logger.info(
            f"creating temporary output folder to store splitted yaml files: '{splitted_output_path}'"
        )
        exec_shell(f"mkdir -p {splitted_output_path}")

    for kustomized_file_name in kustomized_file_list:
        kind_set = set()
        content = load_multiple_yaml_files(
            f"{kustomized_output_files_dir}/{kustomized_file_name}"
        )
        for data in content:
            kind = data["kind"]
            if kind not in kind_set:
                kind_set.add(kind)
                if kind == "CustomResourceDefinition":
                    output_dir = f"{splitted_output_path}/crds"
                else:
                    output_dir = f"{splitted_output_path}/templates/{kind}"

                if os.path.isdir(output_dir) == False:
                    exec_shell(f"mkdir -p {output_dir}")
            if "namespace" in data["metadata"]:
                namespace = data["metadata"]["namespace"]
                name = data["metadata"]["name"]
                output_file_name = f"{name}-{namespace}-{kind}"
            else:
                name = data["metadata"]["name"]
                output_file_name = f"{name}-{kind}"

            # write file into outputFile
            write_yaml_file(
                yaml_content=data, file_path=f"{output_dir}/{output_file_name}.yaml"
            )

        logger.info(f"finished splitting!")


def create_helm_chart(helm_chart_path: str, helm_chart_name: str):
    # if helm chart has been created already, return
    if os.path.exists(f"{helm_chart_path}/Chart.yaml"):
        return

    # make directory for helm chart location if it doesn't exist
    if os.path.isdir(f"{helm_chart_path}") == False:
        exec_shell(f"mkdir -p {helm_chart_path}")
    os.chdir(helm_chart_path)
    exec_shell(f"helm create {helm_chart_name}")
    clean_up_redundant_helm_chart_contents(helm_chart_name)

    # Move chart contents a folder level up for multiple deployment options charts
    # example: kubeflowpipelines/vanilla/kubeflowpipelines -> kubeflowpipelines/vanilla

    source = f"{helm_chart_name}"
    dest = f"./"
    file_list = os.listdir(source)
    for file in file_list:
        shutil.move(f"{source}/{file}", dest)
    # delete folder
    shutil.rmtree(source)

    os.chdir(ROOT_DIR)


def clean_up_redundant_helm_chart_contents(helm_chart_name):
    # cleaning up template folder
    logger.info(f"cleaning up redundant default helm files.")
    dir = f"{helm_chart_name}/templates"
    shutil.rmtree(f"{dir}/tests")
    # delete all autogenerate yaml folders
    filelist = os.listdir(dir)
    for file in filelist:
        if file.endswith(".yaml"):
            os.remove(os.path.join(dir, file))
    # delete NOTES.txt
    os.remove(f"{dir}/NOTES.txt")
    # delete .helmignore
    os.remove(f"{helm_chart_name}/.helmignore")
    logger.info(f"empty out value.yaml file.")
    # empty values.yaml
    value_file = f"{helm_chart_name}/values.yaml"
    empty_yaml_file = None
    write_yaml_file(yaml_content=empty_yaml_file, file_path=value_file)


def move_generated_helm_files_to_folder(dest_dir: str, source_dir: str):
    # move crds
    if os.path.isdir(f"{source_dir}/crds"):
        if os.path.isdir(f"{dest_dir}/crds") == False:
            exec_shell(f"mkdir -p {dest_dir}/crds")
        move_crd_files(dest_dir, f"{source_dir}/crds")

    # move rest of kinds

    move_non_crd_files(f"{dest_dir}/templates", f"{source_dir}/templates")


def move_crd_files(dest_dir: str, source_dir: str):
    filelist = os.listdir(source_dir)
    for file in filelist:
        crd_dest_path = f"{dest_dir}/crds"
        shutil.move(f"{source_dir}/{file}", f"{crd_dest_path}/{file}")

    logger.info(
        f"completed moving Custom Resource Definition yaml files into crds folder."
    )


def move_non_crd_files(dest_dir: str, source_dir: str):
    obj = os.scandir(source_dir)
    logger.info(f"moving the rest of the kinds yaml files into helm templates folder.")
    for entry in obj:
        if entry.is_dir() or entry.is_file():
            # move files to template
            # make new kind folder
            if os.path.isdir(f"{dest_dir}/{entry.name}") == False:
                exec_shell(f"mkdir -p {dest_dir}/{entry.name}")
            filelist = os.listdir(f"{source_dir}/{entry.name}")
            for file in filelist:
                if file.endswith(".yaml"):
                    source = f"{source_dir}/{entry.name}/{file}"
                    dest = f"{dest_dir}/{entry.name}/{file}"
                    shutil.move(source, dest)
    logger.info(
        f"completed moving the rest of the kinds yaml files into helm templates folder."
    )


def find_potential_failed_yaml_files(helm_temp_dir: str):

    problem_filelist = []
    problem_filelist_output_paths = []

    for file_type in POSSIBLE_PROBLEM_FILE_TYPES:
        if os.path.isdir(f"{helm_temp_dir}/templates/{file_type}"):
            logger.info(
                f"finding potential problematic yaml files in {file_type} folder."
            )
            filelist = os.listdir(f"{helm_temp_dir}/templates/{file_type}")
            for file in filelist:
                content = load_multiple_yaml_files(
                    file_path=f"{helm_temp_dir}/templates/{file_type}/{file}"
                )
                for elem in content:
                    find_potential_failed_files_recursive_lookup(
                        elem, problem_filelist, file
                    )

            if problem_filelist:
                if (
                    os.path.isdir(
                        f"{helm_temp_dir}/potential_failed_helm_conversions/{file_type}"
                    )
                    == False
                ):
                    exec_shell(
                        f"mkdir -p {helm_temp_dir}/potential_failed_helm_conversions/{file_type}"
                    )
                logger.info(
                    f"Some Yaml files in {file_type} folder are conflicted with helm template formatting. Please check on files inside failed_helm_conversions folder. Replace all backticks with double quotes, then all {{ with {{`{{ and all }} with }}`}}"
                )
                for file in problem_filelist:
                    source = f"{helm_temp_dir}/templates/{file_type}/{file}"
                    dest = f"{helm_temp_dir}/potential_failed_helm_conversions/{file_type}/{file}"
                    shutil.move(source, dest)
                    problem_filelist_output_paths.append(dest)
    return problem_filelist_output_paths


def find_potential_failed_files_recursive_lookup(
    dictionaries: dict, problem_filelist: list, file: yaml
):
    for k, v in dictionaries.items():
        if isinstance(v, dict):
            find_potential_failed_files_recursive_lookup(v, problem_filelist, file)

        else:
            flag = search(v, "{{") or search(v, "}}")
            if flag:
                problem_filelist.append(file)
                return


def search(value: str, search_for: character):
    n = len(value)
    for i in range(0, n - 1):
        if search_for[0] == value[i] and search_for[1] == value[i + 1]:
            return True
    return False


def clean_up_folder(folder_path: str):
    logger.info(f"deleting folder: {folder_path}")
    shutil.rmtree(f"{folder_path}")
    logger.info("folder deleted.")


def generate_helm_chart(
    kustomize_paths: list,
    helm_chart_name: str,
    output_helm_chart_path: str,
    deployment_option=None,
):
    print_banner(f"==========Converting '{helm_chart_name}'==========")
    if deployment_option:
        print(f"Deployment Option: {deployment_option}")
        kustomized_output_files_dir = (
            f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{helm_chart_name}/{deployment_option}"
        )
        splitted_output_path = f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/splitted_output/{helm_chart_name}/{deployment_option}"
        helm_temp_dir = f"{HELM_TEMP_OUTPUT_PATH}/{helm_chart_name}/{deployment_option}"
    else:
        kustomized_output_files_dir = (
            f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/{helm_chart_name}"
        )
        splitted_output_path = (
            f"{KUSTOMIZED_BUILD_OUTPUT_PATH}/splitted_output/{helm_chart_name}"
        )
        helm_temp_dir = f"{HELM_TEMP_OUTPUT_PATH}/{helm_chart_name}"

    kustomized_file_list = kustomize_build(
        kustomize_paths, helm_chart_name, kustomized_output_files_dir
    )
    split_yaml(kustomized_file_list, splitted_output_path, kustomized_output_files_dir)
    print("Creating Helm Chart Based On Kustomize Build Output")
    create_helm_chart(output_helm_chart_path, helm_chart_name)
    move_generated_helm_files_to_folder(helm_temp_dir, splitted_output_path)
    failed_filelist = find_potential_failed_yaml_files(helm_temp_dir)
    clean_up_folder(splitted_output_path)

    if len(failed_filelist) == 0:
        move_generated_helm_files_to_folder(output_helm_chart_path, helm_temp_dir)
        clean_up_folder(helm_temp_dir)


def main():
    config_file_path = common.CONFIG_FILE
    print_banner("Reading Config")
    cfg = load_yaml_file(file_path=config_file_path)

    for component in Components:
        helm_chart_name = component

        if "deployment_options" in cfg[component]:
            for deployment_option in POSSIBLE_DEPLOYMENT_OPTIONS:
                if deployment_option in cfg[component]["deployment_options"]:
                    kustomize_paths = cfg[component]["deployment_options"][
                        deployment_option
                    ]["kustomization_paths"]
                    output_helm_chart_path = cfg[component]["deployment_options"][
                        deployment_option
                    ]["output_helm_chart_path"]
                    generate_helm_chart(
                        kustomize_paths,
                        helm_chart_name,
                        output_helm_chart_path,
                        deployment_option,
                    )
        else:
            kustomize_paths = cfg[component]["kustomization_paths"]
            output_helm_chart_path = cfg[component]["output_helm_chart_path"]
            generate_helm_chart(
                kustomize_paths, helm_chart_name, output_helm_chart_path
            )


if __name__ == "__main__":
    main()
