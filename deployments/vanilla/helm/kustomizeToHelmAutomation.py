
import yaml
import os
import shutil

def main():
    curdir = os.getcwd()
    kustomized_path = getKustomizedPath()
    helmChartName = input("Please input the name of the helm chart: ")
    kustomizeBuild(kustomized_path, helmChartName)
    moveKustomizedFileToCurdir(kustomized_path, curdir, helmChartName)
    splitYAML(curdir, helmChartName)
    createHelmChart(curdir, helmChartName)
    moveYAMLFilesToHelmTemplate(curdir,helmChartName)
    findFailedConfigFiles(curdir, helmChartName)
    cleanup(curdir)

def getKustomizedPath():
    kustomized_path = input("input kustomization.yaml absolute path for helm chart convertion: ")
    if kustomized_path.split("/")[-1] == "kustomization.yaml" :
        kustomized_path = "/".join(kustomized_path.split("/")[:-1])
    if os.path.isdir(kustomized_path) == False:
        raise TypeError("The input path must be a valid path in the directory")
    
    #check if there is kustomization.yaml in the directory
    if not os.path.exists(f"{kustomized_path}/kustomization.yaml"):
        raise ValueError("The input path must contains kustomization.yaml file")
    return kustomized_path

def kustomizeBuild(kustomized_path,helmChartName):

    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    command = f"cd {kustomized_path}; kustomize build . > {KustomizedFileName}"
    os.system(command)
    if not os.path.exists(f"{kustomized_path}/{helmChartName}-kustomized.yaml"):
        raise ValueError("kustomized yaml file is not generated.")


def moveKustomizedFileToCurdir(source, dest, helmChartName):
    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    sourceFull = f"{source}/{KustomizedFileName}"
    dest = f"{dest}/{KustomizedFileName}"
    shutil.move(sourceFull,dest)

def splitYAML(curdir,helmChartName):
    kindSet = set()
    KustomizedFileName = f"{helmChartName}-kustomized.yaml"
    outputPath = f"{curdir}/output"
    if os.path.isdir(outputPath) == False:
        os.mkdir(outputPath)
    with open(KustomizedFileName) as file:
        for data in yaml.safe_load_all(file):
            kind = data['kind'] 
            if kind not in kindSet:
                kindSet.add(kind)
                if os.path.isdir(f"output/{kind}") == False:
                    os.mkdir(f"output/{kind}")
            if 'namespace' in data['metadata']:
                namespace = data['metadata']['namespace']
                name = data['metadata']['name']
                outputFileName = f"{name}-{namespace}-{kind}"
            else:
                name = data['metadata']['name']
                outputFileName = f"{name}-{kind}"
        #write file into outputFile
            with open(f"{outputFileName}.yaml",'w')as file:
                yaml.dump(data, file)
                #move file to folder
                source = f"{curdir}/{outputFileName}.yaml"
                dest = f"{curdir}/output/{kind}/{outputFileName}.yaml"
                shutil.move(source,dest)
                    

def createHelmChart(curdir,helmChartName):
    os.system(f"helm create {helmChartName}")
    if not os.path.exists(f"{curdir}/{helmChartName}"):
        raise ValueError ("helm chart was not created successfully.")

    #cleaning up template folder
    dir = f"{curdir}/{helmChartName}/templates"
    shutil.rmtree(f"{dir}/tests")
    #delete all autogenerate yaml folders
    filelist = [ f for f in os.listdir(dir) if f.endswith(".yaml") ]
    for f in filelist:
        os.remove(os.path.join(dir, f))
    #delete NOTES.txt
    os.remove(f"{dir}/NOTES.txt")

    #empty values.yaml
    valueFile = f"{curdir}/{helmChartName}/values.yaml"
    emptyYAMLFile = None
    with open(valueFile,'w') as file:
        yaml.dump(emptyYAMLFile, file)
        file.close()
    
  


def moveYAMLFilesToHelmTemplate(curdir,helmChartName):
    outputPath = f"{curdir}/output"
    
    dir = f"{curdir}/{helmChartName}"
    #move crds
    if os.path.isdir(f"{dir}/crds") == False:
        os.mkdir(f"{dir}/crds")
    if os.path.isdir(f"{outputPath}/CustomResourceDefinition"):
        filelist = [ f for f in os.listdir(f"{outputPath}/CustomResourceDefinition")]
        crdDestPath = f"{dir}/crds"
        for f in filelist:
            shutil.move(f"{outputPath}/CustomResourceDefinition/{f}",f"{crdDestPath}/{f}")
    
    #move rest of kinds
    obj = os.scandir(outputPath)
    
    for entry in obj :
        if entry.is_dir() or entry.is_file():
            #move files to template
            if (entry.name != 'CustomResourceDefinition'):
                if os.path.isdir(f"{curdir}/{helmChartName}/templates/{entry.name}") == False:
                    os.mkdir(f"{curdir}/{helmChartName}/templates/{entry.name}")
                filelist = [ f for f in os.listdir(f"{outputPath}/{entry.name}") if f.endswith(".yaml") ]
                for f in filelist:
                    source = f"{outputPath}/{entry.name}/{f}"
                    dest = f"{curdir}/{helmChartName}/templates/{entry.name}/{f}"
                    shutil.move(source,dest)

def findFailedConfigFiles (curdir, helmChartName):
    dir = f"{curdir}/{helmChartName}"
    problemFileList = []
    if os.path.isdir(f"{dir}/templates/ConfigMap"):
        filelist = [ f for f in os.listdir(f"{dir}/templates/ConfigMap")]
        for f in filelist:
            with open (f"{dir}/templates/ConfigMap/{f}") as file:
                for elem in yaml.safe_load_all(file):
                    findFailedFilesRecursiveLookup(elem,problemFileList,f)
                        
        
        if problemFileList:
            if os.path.isdir(f"{curdir}/{helmChartName}/failed_helm_conversions") == False:
                os.mkdir(f"{curdir}/{helmChartName}/failed_helm_conversions")
            print("Some Config files are conflicted with helm template formatting. Please check on files inside failed_helm_conversions folder. Replace all backticks with double quotes, then all {{ with {{`{{ and all }} with }}`}}")
            for file in problemFileList:
                source = f"{curdir}/{helmChartName}/templates/ConfigMap/{file}"
                dest = f"{curdir}/{helmChartName}/failed_helm_conversions/{file}"
                shutil.move(source,dest)

def findFailedFilesRecursiveLookup(d, problemFileList, f):
    for k, v in d.items():
        if isinstance(v, dict):
            findFailedFilesRecursiveLookup(v, problemFileList, f)
            
        else:
            flag = search(v,'`')
            if flag:
                problemFileList.append(f)
                return
                   
def search(value, searchFor):
    for v in value:
        if searchFor in v:
            return True
    return False


def cleanup(curdir):
    shutil.rmtree(f"{curdir}/output")

if __name__ == "__main__":
    main()
