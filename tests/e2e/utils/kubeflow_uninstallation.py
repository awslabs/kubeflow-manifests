from e2e.utils.utils import print_banner
import argparse
from e2e.utils.utils import (
    kubectl_delete,
    kubectl_delete_crd,
    uninstall_helm,
    delete_kustomize,
    load_yaml_file,
)
import os
import subprocess


INSTALLATION_PATH_FILE_VANILLA = "./resources/installation_config/vanilla.yaml"
INSTALLATION_PATH_FILE_COGNITO = "./resources/installation_config/cognito.yaml"
INSTALLATION_PATH_FILE_RDS_S3 = "./resources/installation_config/rds-s3.yaml"
INSTALLATION_PATH_FILE_RDS_ONLY = "./resources/installation_config/rds-only.yaml"
INSTALLATION_PATH_FILE_S3_ONLY = "./resources/installation_config/s3-only.yaml"
INSTALLATION_PATH_FILE_COGNITO_RDS_S3 = "./resources/installation_config/cognito-rds-s3.yaml"

Uninstall_Sequence = [
    "aws-authservice",
    "ingress",
    "aws-load-balancer-controller",
    "ack-sagemaker-controller",
    "user-namespace",
    "profiles-and-kfam",
    "tensorboard-controller",
    "tensorboards-web-app",
    "katib",
    "training-operator",
    "volumes-web-app",
    "notebook-controller",
    "jupyter-web-app",
    "admission-webhook",
    "kubeflow-pipelines",
    "aws-secrets-manager",
    "central-dashboard",
    "models-web-app",
    "kserve",
    "knative-eventing",
    "knative-serving",
    "kubeflow-issuer",
    "kubeflow-roles",
    "kubeflow-istio-resources",
    "kubeflow-namespace",
    "cluster-local-gateway",
    "oidc-authservice",
    "dex",
    "istio-1-14",
    "cert-manager",
]


def uninstall_kubeflow(installation_option, deployment_option):
    

    if deployment_option == "vanilla":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_VANILLA)
    elif deployment_option == "cognito":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_COGNITO)
    elif deployment_option == "rds-s3":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_RDS_S3)
    elif deployment_option == "rds-only":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_RDS_ONLY)
    elif deployment_option == "s3-only":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_S3_ONLY)
    elif deployment_option == "cognito-rds-s3":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_COGNITO_RDS_S3)

    print_banner(
        f"You are uninstalling kubeflow {deployment_option} deployment with {installation_option}"
    )

    for component in Uninstall_Sequence:
        if component == "cert-manager":
            namespace = "cert-manager"
        elif component == "aws-load-balancer-controller":
            namespace = "kube-system"
        else:
            namespace = None
        delete_component(
            installation_option, deployment_option, path_dic, component, namespace
        )



def delete_component(
    installation_option, deployment_option, path_dic, component_name, namespace
):
    print(f"==========uninstallating {component_name}...==========")
    if component_name not in path_dic:
        print(
            f"component {component_name} is not applicable for deployment option: {deployment_option}"
        )
        return
    else:
        installation_path = path_dic[component_name]["installation_options"][
            installation_option
        ]

        if installation_option == "helm":
            if component_name == "kubeflow-namespace":
                for kustomize_path in path_dic[component_name]["installation_options"]["kustomize"]:
                    delete_kustomize(kustomize_path)

            elif component_name == "ingress":
                uninstall_helm(component_name, namespace)
                #Helm doesn't seem to delete ingress during uninstall
                retcode = subprocess.call(f"kubectl delete ingress -n istio-system istio-ingress".split())
                assert retcode == 0
            else:
                uninstall_helm(component_name, namespace)
                if os.path.isdir(f"{installation_path}/crds"):
                    print(f"deleting {component_name} crds ...")
                    kubectl_delete(f"{installation_path}/crds")
                # delete aws-load-balancer-controller crds for official helm chart
                if component_name == "aws-load-balancer-controller":
                    kubectl_delete(
                        "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/6d3e976e3f60dc4588c01bad036d77c127a68e71/helm/aws-load-balancer-controller/crds/crds.yaml"
                    )
        # kustomize
        else:
            installation_path.reverse()
            for kustomize_path in installation_path:
                delete_kustomize(kustomize_path)

    # clear up implicit crd resources for Dex
    if component_name == "dex":
        kubectl_delete_crd("authrequests.dex.coreos.com")
        kubectl_delete_crd("connectors.dex.coreos.com")
        kubectl_delete_crd("devicerequests.dex.coreos.com")
        kubectl_delete_crd("devicetokens.dex.coreos.com")
        kubectl_delete_crd("oauth2clients.dex.coreos.com")
        kubectl_delete_crd("offlinesessionses.dex.coreos.com")
        kubectl_delete_crd("passwords.dex.coreos.com")
        kubectl_delete_crd("refreshtokens.dex.coreos.com")
        kubectl_delete_crd("signingkeies.dex.coreos.com")

    print(f"All {component_name} resources are cleared!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    INSTALLATION_OPTION_DEFAULT = "kustomize"
    parser.add_argument(
        "--installation_option",
        type=str,
        default=INSTALLATION_OPTION_DEFAULT,
        help=f"Kubeflow Installation option default is set to {INSTALLATION_OPTION_DEFAULT}",
        choices=['kustomize','helm'],
        required=False,
    )
    
    DEPLOYMENT_OPTION_DEFAULT = "vanilla"
    parser.add_argument(
        "--deployment_option",
        type=str,
        default=DEPLOYMENT_OPTION_DEFAULT,
        choices=['vanilla','cognito','rds-s3','rds-only','s3-only','cognito-rds-s3'],
        help=f"Kubeflow deployment options default is set to {DEPLOYMENT_OPTION_DEFAULT}",
        required=False,
    )

    args, _ = parser.parse_known_args()

    uninstall_kubeflow(args.installation_option,  args.deployment_option)
