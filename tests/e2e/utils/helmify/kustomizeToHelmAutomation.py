import logging

import os
import shutil
from numpy import character

import yaml
from e2e.utils.utils import print_banner, load_yaml_file, load_multiple_yaml_files, write_yaml_file
from e2e.utils.helmify import common

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    config_file_path = common.CONFIG_FILE
    print_banner("Reading Config")
    cfg = load_yaml_file(file_path=config_file_path)
    kustomized_path = cfg["Kustomization Filepath"]
    helm_chart_name = cfg["Helm Chart Name"]
    helm_chart_path = cfg["Output Helm Filepath"]
    curdir = f"{os.getcwd()}"
    print_banner("Creating Kustomize Build Yaml File ")
    kustomizeBuild(kustomized_path, helm_chart_name)
    moveKustomizedFileToCurdir(kustomized_path, curdir, helm_chart_name)
    print_banner("Splitting Consolidated Kustomize Build Yaml File into Individual Files")
    splitYAML(curdir, helm_chart_name)
    print_banner("Creating Helm Chart Based On Kustomize Build Output")
    createHelmChart(helm_chart_path, helm_chart_name)
    moveYAMLFilesToHelmTemplate(curdir,helm_chart_path,helm_chart_name)
    findFailedConfigFiles(helm_chart_path, helm_chart_name)
    cleanup(curdir)
    print_banner("Generating Consolidated Helm Manifest")
    generateHelmTemplate(helm_chart_path,helm_chart_name,curdir)

def kustomizeBuild(kustomized_path: str, helmChartName: str):

    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    os.chdir(f"{kustomized_path}")
    command = f"kustomize build . > {KustomizedFileName}"
    os.system(command)
    logger.info(f"kustomize build completed, file is saved in '{kustomized_path}/{KustomizedFileName}'")
    if not os.path.exists(f"{kustomized_path}/{helmChartName}-kustomized.yaml"):
        raise ValueError("kustomized yaml file is not generated.")


def moveKustomizedFileToCurdir(source: str, dest: str, helmChartName: str):
    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    sourceFull = f"{source}/{KustomizedFileName}"
    destFull = f"{dest}/{KustomizedFileName}"
    logger.info(f"moving consolidated kustomized manifest file to current working directory: {destFull}'")
    shutil.move(sourceFull,destFull)

def splitYAML(curdir: str ,helmChartName: str):
    kindSet = set()
    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    outputPath = f"{curdir}/output"
    logger.info(f"creating temporary output folder to store splitted yaml files: '{outputPath}'")
    if os.path.isdir(outputPath) == False:
        os.mkdir(outputPath)
    
    content = load_multiple_yaml_files(file_path=f"{curdir}/{KustomizedFileName}")
    for data in content:
        kind = data['kind'] 
        if kind not in kindSet:
            kindSet.add(kind)
            if os.path.isdir(f"{curdir}/output/{kind}") == False:
                os.mkdir(f"{curdir}/output/{kind}")
        if 'namespace' in data['metadata']:
            namespace = data['metadata']['namespace']
            name = data['metadata']['name']
            outputFileName = f"{name}-{namespace}-{kind}"
        else:
            name = data['metadata']['name']
            outputFileName = f"{name}-{kind}"

        #write file into outputFile
        write_yaml_file(yaml_content=data, file_path=f"{curdir}/{outputFileName}.yaml")

        #move file to folder
        source = f"{curdir}/{outputFileName}.yaml"
        dest = f"{curdir}/output/{kind}/{outputFileName}.yaml"
        shutil.move(source,dest)

    logger.info(f"finished splitting!")
                    

def createHelmChart(helm_chart_path: str, helm_chart_name: str):
    os.chdir(f"{helm_chart_path}")
    os.system(f"helm create {helm_chart_name}")
    if not os.path.exists(f"{helm_chart_path}/{helm_chart_name}"):
        raise ValueError ("helm chart was not created successfully.")

    #cleaning up template folder
    logger.info(f"cleaning up redundant default helm files.")
    dir = f"{helm_chart_path}/{helm_chart_name}/templates"
    shutil.rmtree(f"{dir}/tests")
    #delete all autogenerate yaml folders
    filelist = [ f for f in os.listdir(dir) if f.endswith(".yaml") ]
    for f in filelist:
        os.remove(os.path.join(dir, f))
    #delete NOTES.txt
    os.remove(f"{dir}/NOTES.txt")

    logger.info(f"empty out value.yaml file.")
    #empty values.yaml
    valueFile = f"{helm_chart_path}/{helm_chart_name}/values.yaml"
    emptyYAMLFile = None
    write_yaml_file(yaml_content=emptyYAMLFile, file_path=valueFile)
    
  


def moveYAMLFilesToHelmTemplate(curdir: str, helm_chart_path: str, helm_chart_name: str):
    outputPath = f"{curdir}/output"
    helm_dir = f"{helm_chart_path}/{helm_chart_name}"
    #move crds
    if os.path.isdir(f"{helm_dir}/crds") == False:
        os.mkdir(f"{helm_dir}/crds")
        logger.info(f"created crds folder inside helm chart for Custom Resource Definition yaml files.")
    if os.path.isdir(f"{outputPath}/CustomResourceDefinition"):
        logger.info(f"moving Custom Resource Definition yaml files into crds folder.")
        filelist = [ f for f in os.listdir(f"{outputPath}/CustomResourceDefinition")]
        crdDestPath = f"{helm_dir}/crds"
        for f in filelist:
            shutil.move(f"{outputPath}/CustomResourceDefinition/{f}",f"{crdDestPath}/{f}")
    
    logger.info(f"completed moving Custom Resource Definition yaml files into crds folder.")
    #move rest of kinds
    obj = os.scandir(outputPath)
    logger.info(f"moving the rest of the kinds yaml files into helm templates folder.")
    for entry in obj :
        if entry.is_dir() or entry.is_file():
            #move files to template
            if (entry.name != 'CustomResourceDefinition'):
                if os.path.isdir(f"{helm_dir}/templates/{entry.name}") == False:
                    os.mkdir(f"{helm_dir}/templates/{entry.name}")
                filelist = [ f for f in os.listdir(f"{outputPath}/{entry.name}") if f.endswith(".yaml") ]
                for f in filelist:
                    source = f"{outputPath}/{entry.name}/{f}"
                    dest = f"{helm_dir}/templates/{entry.name}/{f}"
                    shutil.move(source,dest)
    logger.info(f"completed moving the rest of the kinds yaml files into helm templates folder.")

def findFailedConfigFiles (helm_chart_path: str, helm_chart_name: str):
    dir = f"{helm_chart_path}/{helm_chart_name}"
    problemFileList = []
    
    if os.path.isdir(f"{dir}/templates/ConfigMap"):
        logger.info(f"finding potential problematic config yaml files.")
        filelist = [ f for f in os.listdir(f"{dir}/templates/ConfigMap")]
        for f in filelist:
            content = load_multiple_yaml_files(file_path=f"{dir}/templates/ConfigMap/{f}") 
            for elem in content:
                findFailedFilesRecursiveLookup(elem,problemFileList,f)
                        
        
        if problemFileList:
            if os.path.isdir(f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions") == False:
                os.mkdir(f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions")
            logger.info("Some Config files are conflicted with helm template formatting. Please check on files inside failed_helm_conversions folder. Replace all backticks with double quotes, then all {{ with {{`{{ and all }} with }}`}}")
            for file in problemFileList:
                source = f"{helm_chart_path}/{helm_chart_name}/templates/ConfigMap/{file}"
                dest = f"{helm_chart_path}/{helm_chart_name}/failed_helm_conversions/{file}"
                shutil.move(source,dest)

def findFailedFilesRecursiveLookup(dictionaries: dict, problemFileList: list, f: yaml):
    for k, v in dictionaries.items():
        if isinstance(v, dict):
            findFailedFilesRecursiveLookup(v, problemFileList, f)
            
        else:
            flag = search(v,'`')
            if flag:
                problemFileList.append(f)
                return
                   
def search(value: str, searchFor: character):
    for v in value:
        if searchFor in v:
            return True
    return False


def cleanup(curdir: str):
    logger.info(f"deleting temporary output folder: {curdir}/output")
    shutil.rmtree(f"{curdir}/output")
    logger.info("folder deleted.")

def generateHelmTemplate(helm_chart_path, helm_chart_name, curdir):
    os.chdir(f"{helm_chart_path}")
    logger.info("creating a copy of existing helm chart folder.")
    shutil.copytree(f"{helm_chart_path}/{helm_chart_name}",f"{helm_chart_path}/{helm_chart_name}_copy")
    copy_helm_path = f"{helm_chart_path}/{helm_chart_name}_copy"
    os.chdir(copy_helm_path)
    #move crds and failed_helm_conversions files to template folder
    logger.info("moving crds and failed_helm_conversions files to template folder")
    if os.path.isdir(f"{copy_helm_path}/failed_helm_conversions"):
        for file in os.listdir(f"{copy_helm_path}/failed_helm_conversions"):
            source = f"{copy_helm_path}/failed_helm_conversions/{file}"
            dest = f"{copy_helm_path}/templates/{file}"
            shutil.move(source,dest)
    
    if os.path.isdir(f"{copy_helm_path}/crds"):
        for file in os.listdir(f"{copy_helm_path}/crds"):
            source = f"{copy_helm_path}/crds/{file}"
            dest = f"{copy_helm_path}/templates/{file}"
            shutil.move(source,dest)

    Helmified_file_name = f"{helm_chart_name}-helmified.yaml"

    os.system(f"helm template . > {Helmified_file_name}")
    #move the helmified file out
    shutil.move(f"{copy_helm_path}/{Helmified_file_name}",f"{curdir}/{Helmified_file_name}")
    logger.info(f"created consolidated helm yaml file in: '{curdir}/{Helmified_file_name}'.")

    #delete the copy helm folder
    os.chdir(f"{helm_chart_path}")
    shutil.rmtree(f"{copy_helm_path }")
    logger.info(f"deleted the copy helm folder.")


if __name__ == "__main__":
    main()