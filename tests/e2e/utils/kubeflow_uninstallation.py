from e2e.utils.utils import print_banner
import argparse
from e2e.utils.utils import (
    kubectl_delete,
    kubectl_delete_crd,
    uninstall_helm,
    delete_kustomize,
    load_yaml_file,
    exec_shell,
    check_helm_chart_exists,
)
import os
import subprocess


INSTALLATION_CONFIG_VANILLA = "./resources/installation_config/vanilla.yaml"
INSTALLATION_CONFIG_COGNITO = "./resources/installation_config/cognito.yaml"
INSTALLATION_CONFIG_RDS_S3 = "./resources/installation_config/rds-s3.yaml"
INSTALLATION_CONFIG_RDS_ONLY = "./resources/installation_config/rds-only.yaml"
INSTALLATION_CONFIG_S3_ONLY = "./resources/installation_config/s3-only.yaml"
INSTALLATION_CONFIG_COGNITO_RDS_S3 = (
    "./resources/installation_config/cognito-rds-s3.yaml"
)
INSTALLATION_CONFIG_S3_ONLY_STATIC = (
    "./resources/installation_config/s3-only-static.yaml"
)
INSTALLATION_CONFIG_RDS_S3_STATIC = "./resources/installation_config/rds-s3-static.yaml"
INSTALLATION_CONFIG_COGNITO_RDS_S3_STATIC = (
    "./resources/installation_config/cognito-rds-s3-static.yaml"
)

Uninstall_Sequence = [
    "aws-authservice",
    "ingress",
    "aws-load-balancer-controller",
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
    "istio",
    "cert-manager",
    "aws-telemetry",
    "ack-sagemaker-controller",
]


def uninstall_kubeflow(
    installation_option, deployment_option, pipeline_s3_credential_option
):

    if deployment_option == "vanilla":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_VANILLA)
    elif deployment_option == "cognito":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_COGNITO)
    elif deployment_option == "rds-s3" and pipeline_s3_credential_option == "static":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_RDS_S3_STATIC)
    elif deployment_option == "s3-only" and pipeline_s3_credential_option == "static":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_S3_ONLY_STATIC)
    elif (
        deployment_option == "cognito-rds-s3"
        and pipeline_s3_credential_option == "static"
    ):
        path_dic = load_yaml_file(INSTALLATION_CONFIG_COGNITO_RDS_S3_STATIC)
    elif deployment_option == "rds-s3":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_RDS_S3)
    elif deployment_option == "rds-only":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_RDS_ONLY)
    elif deployment_option == "s3-only":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_S3_ONLY)
    elif deployment_option == "cognito-rds-s3":
        path_dic = load_yaml_file(INSTALLATION_CONFIG_COGNITO_RDS_S3)

    print_banner(
        f"You are uninstalling kubeflow {deployment_option} deployment with {installation_option} with {pipeline_s3_credential_option}"
    )

    for component in Uninstall_Sequence:
        if component == "cert-manager":
            namespace = "cert-manager"
        elif component == "aws-load-balancer-controller":
            namespace = "kube-system"
        elif component == "ack-sagemaker-controller":
            namespace = "ack-system"
        else:
            namespace = None
        delete_component(installation_option, path_dic, component, namespace)


def delete_component(
    installation_option, installation_config, component_name, namespace
):
    if component_name not in installation_config:
        return
    else:
        print(f"==========uninstallating {component_name}...==========")
        # remote
        if (
            "repo"
            in installation_config[component_name]["installation_options"][
                installation_option
            ]
        ):
            uninstall_remote_component(component_name, namespace)
        # local
        else:
            installation_path = installation_config[component_name][
                "installation_options"
            ][installation_option]["paths"]

            if installation_option == "helm":
                if component_name == "kubeflow-namespace":
                    for kustomize_path in installation_config[component_name][
                        "installation_options"
                    ]["kustomize"]["paths"]:
                        delete_kustomize(kustomize_path)
                else:
                    if check_helm_chart_exists(component_name, namespace):
                        uninstall_helm(component_name, namespace)
                        if component_name == "ingress":
                            # Helm doesn't seem to delete ingress during uninstall
                            exec_shell(
                                f"kubectl delete ingress -n istio-system istio-ingress"
                            )
                    if os.path.isdir(f"{installation_path}/crds"):
                        print(f"deleting {component_name} crds ...")
                        kubectl_delete(f"{installation_path}/crds")
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


def uninstall_remote_component(component_name, namespace):
    if check_helm_chart_exists(component_name, namespace):
        uninstall_helm(component_name, namespace)
        if component_name == "aws-load-balancer-controller":
            kubectl_delete(
                "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/6d3e976e3f60dc4588c01bad036d77c127a68e71/helm/aws-load-balancer-controller/crds/crds.yaml"
            )
        elif component_name == "ack-sagemaker-controller":
            kubectl_delete(f"../../charts/common/ack-controller/sagemaker-chart/crds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    INSTALLATION_OPTION_DEFAULT = "kustomize"
    parser.add_argument(
        "--installation_option",
        type=str,
        default=INSTALLATION_OPTION_DEFAULT,
        help=f"Kubeflow Installation option default is set to {INSTALLATION_OPTION_DEFAULT}",
        choices=["kustomize", "helm"],
        required=False,
    )

    DEPLOYMENT_OPTION_DEFAULT = "vanilla"
    parser.add_argument(
        "--deployment_option",
        type=str,
        default=DEPLOYMENT_OPTION_DEFAULT,
        choices=[
            "vanilla",
            "cognito",
            "rds-s3",
            "rds-only",
            "s3-only",
            "cognito-rds-s3",
        ],
        help=f"Kubeflow deployment options default is set to {DEPLOYMENT_OPTION_DEFAULT}",
        required=False,
    )

    PIPELINE_S3_CREDENTIAL_OPTION_DEFAULT = "irsa"
    parser.add_argument(
        "--pipeline_s3_credential_option",
        type=str,
        default=PIPELINE_S3_CREDENTIAL_OPTION_DEFAULT,
        choices=["irsa", "static"],
        help=f"Kubeflow default credential option default is set to irsa",
        required=False,
    )

    args, _ = parser.parse_known_args()

    uninstall_kubeflow(
        args.installation_option,
        args.deployment_option,
        args.pipeline_s3_credential_option,
    )
