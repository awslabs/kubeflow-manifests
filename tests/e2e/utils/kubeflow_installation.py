from retrying import retry
from e2e.utils.utils import load_yaml_file, print_banner
import argparse
from e2e.utils.utils import (
    kubectl_wait_pods,
    apply_kustomize,
    install_helm,
    exec_shell,
    get_variable_from_params,
)
import subprocess
import os
import time

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


Install_Sequence = [
    "cert-manager",
    "istio",
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
    "ack-sagemaker-controller",
    "ingress",
    "aws-load-balancer-controller",
    "aws-authservice",
]


def install_kubeflow(
    installation_option,
    deployment_option,
    cluster_name,
    pipeline_s3_credential_option,
    aws_telemetry=True,
):
    print(cluster_name)
    if deployment_option == "vanilla":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_VANILLA)
    elif deployment_option == "cognito":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_COGNITO)
    elif deployment_option == "rds-s3" and pipeline_s3_credential_option == "static":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_RDS_S3_STATIC)
    elif deployment_option == "s3-only" and pipeline_s3_credential_option == "static":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_S3_ONLY_STATIC)
    elif (
        deployment_option == "cognito-rds-s3"
        and pipeline_s3_credential_option == "static"
    ):
        installation_config = load_yaml_file(INSTALLATION_CONFIG_COGNITO_RDS_S3_STATIC)
    elif deployment_option == "rds-s3":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_RDS_S3)
    elif deployment_option == "rds-only":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_RDS_ONLY)
    elif deployment_option == "s3-only":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_S3_ONLY)
    elif deployment_option == "cognito-rds-s3":
        installation_config = load_yaml_file(INSTALLATION_CONFIG_COGNITO_RDS_S3)

    print_banner(
        f"Installing kubeflow {deployment_option} deployment with {installation_option} with {pipeline_s3_credential_option}"
    )

    for component in Install_Sequence:
        install_component(
            installation_option,
            component,
            installation_config,
            cluster_name,
            pipeline_s3_credential_option,
        )

    if aws_telemetry == True:
        install_component(
            installation_option,
            "aws-telemetry",
            installation_config,
            cluster_name,
            pipeline_s3_credential_option,
        )


def install_component(
    installation_option,
    component_name,
    installation_config,
    cluster_name,
    pipeline_s3_credential_option,
    crd_established=True,
):
    # component not applicable for deployment option
    if component_name not in installation_config:
        return
    else:
        print(f"==========Installing {component_name}==========")
        # remote repo
        if (
            "repo"
            in installation_config[component_name]["installation_options"][
                installation_option
            ]
        ):
            install_remote_component(component_name, cluster_name)
        # local repo
        else:
            installation_paths = installation_config[component_name][
                "installation_options"
            ][installation_option]["paths"]
            # helm
            if installation_option == "helm":
                ##deal with namespace already exist issue for rds-s3 auto set-up script
                if component_name == "kubeflow-namespace":
                    for kustomize_path in installation_config[component_name][
                        "installation_options"
                    ]["kustomize"]["paths"]:
                        apply_kustomize(kustomize_path)
                else:
                    install_helm(component_name, installation_paths)
            # kustomize
            else:
                # crd required to established for installation
                if (
                    "validations" in installation_config[component_name]
                    and "crds" in installation_config[component_name]["validations"]
                ):
                    print("need to wait for crds....")
                    crds = installation_config[component_name]["validations"]["crds"]
                    crd_established = False
                for kustomize_path in installation_paths:
                    if not crd_established:
                        apply_kustomize(kustomize_path, crds)
                        crd_established = True
                    else:
                        apply_kustomize(kustomize_path)
                # TO DO: Debug and add additional validation step for cert-manager resources in future for kubeflow-issuer to be installed
                # temporary solution to wait for 60s
                if component_name == "cert-manager":
                    print(
                        "wait for 60s for cert-manager-webhook resource to be ready..."
                    )
                    time.sleep(60)

        if "validations" in installation_config[component_name]:
            validate_component_installation(installation_config, component_name)
        print(f"All {component_name} pods are running!")


@retry(stop_max_attempt_number=3, wait_fixed=15000)
def validate_component_installation(installation_config, component_name):
    labels = installation_config[component_name]["validations"]["pods"]["labels"]
    namespace = installation_config[component_name]["validations"]["pods"]["namespace"]
    for label in labels:
        key = label["key"]
        value = label["value"]
        print(f"Waiting for {component_name} pods to be ready ...")
        kubectl_wait_pods(value, namespace, key)


def install_remote_component(component_name, cluster_name):
    # cert-manager official chart command call
    if component_name == "cert-manager":
        install_certmanager()
    elif component_name == "aws-load-balancer-controller":
        install_alb_controller(cluster_name)
    elif component_name == "ack-sagemaker-controller":
        install_ack_controller()


def install_certmanager():
    exec_shell(f"helm repo add jetstack https://charts.jetstack.io")
    exec_shell(f"helm repo update")
    exec_shell(
        f"helm upgrade --install cert-manager jetstack/cert-manager \
                        --namespace cert-manager \
                        --create-namespace \
                        --version v1.10.1 \
                        --set installCRDs=true"
    )


def install_alb_controller(cluster_name):
    exec_shell(f"helm repo add eks https://aws.github.io/eks-charts")

    exec_shell(f"helm repo update")

    exec_shell(
        f"helm upgrade --install aws-load-balancer-controller eks/aws-load-balancer-controller \
            -n kube-system \
            --set clusterName={cluster_name} \
            --set serviceAccount.create=false \
            --set serviceAccount.name=aws-load-balancer-controller \
            --version v1.4.8"
    )


def install_ack_controller():
    SERVICE = "sagemaker"
    RELEASE_VERSION = "v1.2.1"
    CHART_EXPORT_PATH = "../../charts/common/ack-controller"
    CHART_REF = f"{SERVICE}-chart"
    CHART_REPO = f"public.ecr.aws/aws-controllers-k8s/{CHART_REF}"
    CHART_PACKAGE = f"{CHART_REF}-{RELEASE_VERSION}.tgz"
    ACK_K8S_NAMESPACE = "ack-system"
    cfg = load_yaml_file(file_path="./utils/ack_sm_controller_bootstrap/config.yaml")
    IAM_ROLE_ARN_FOR_IRSA = cfg["ack_sagemaker_oidc_role"]
    ACK_AWS_REGION = cfg["cluster"]["region"]

    exec_shell(f"mkdir -p {CHART_EXPORT_PATH}")
    exec_shell(
        f"aws ecr-public get-login-password --region us-east-1 | "
        + "helm registry login --username AWS --password-stdin public.ecr.aws"
    )
    exec_shell(
        f"helm pull oci://{CHART_REPO} --version {RELEASE_VERSION} -d {CHART_EXPORT_PATH}"
    )
    exec_shell(f"tar xvf {CHART_EXPORT_PATH}/{CHART_PACKAGE} -C {CHART_EXPORT_PATH}")
    exec_shell(
        f"yq e '.aws.region=\"{ACK_AWS_REGION}\"' -i {CHART_EXPORT_PATH}/{SERVICE}-chart/values.yaml"
    )
    exec_shell(
        f'yq e \'.serviceAccount.annotations."eks.amazonaws.com/role-arn"="{IAM_ROLE_ARN_FOR_IRSA}"\' '
        + f"-i {CHART_EXPORT_PATH}/{SERVICE}-chart/values.yaml"
    )
    exec_shell(
        f'yq e \'.role.labels."rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit"="true"\' '
        + f"-i {CHART_EXPORT_PATH}/{SERVICE}-chart/values.yaml"
    )
    exec_shell(
        f"helm upgrade --install -n {ACK_K8S_NAMESPACE} --create-namespace ack-{SERVICE}-controller "
        f"{CHART_EXPORT_PATH}/{SERVICE}-chart"
    )


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

    parser.add_argument(
        "--aws_telemetry",
        type=bool,
        default=True,
        help=f"AWS Telemetry tracking",
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

    parser.add_argument(
        "--cluster_name",
        type=str,
        help=f"EKS cluster Name",
        required=True,
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

    install_kubeflow(
        args.installation_option,
        args.deployment_option,
        args.cluster_name,
        args.pipeline_s3_credential_option,
        args.aws_telemetry,
    )
