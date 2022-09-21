from retrying import retry
from e2e.utils.utils import load_yaml_file, print_banner
import argparse
from e2e.utils.utils import (
    kubectl_wait_pods,
    apply_kustomize,
    install_helm,
    exec_shell,
    get_variable_from_params,
    find_and_replace_in_file,
)
import subprocess
import os
import time

INSTALLATION_PATH_FILE_VANILLA = "./resources/installation_config/vanilla.yaml"
INSTALLATION_PATH_FILE_COGNITO = "./resources/installation_config/cognito.yaml"
INSTALLATION_PATH_FILE_RDS_S3 = "./resources/installation_config/rds-s3.yaml"
INSTALLATION_PATH_FILE_RDS_ONLY = "./resources/installation_config/rds-only.yaml"
INSTALLATION_PATH_FILE_S3_ONLY = "./resources/installation_config/s3-only.yaml"
INSTALLATION_PATH_FILE_COGNITO_RDS_S3 = "./resources/installation_config/cognito-rds-s3.yaml"

Install_Sequence = [
    "cert-manager",
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
    "ack-sagemaker-controller",
    "ingress",
    "aws-load-balancer-controller",
    "aws-authservice",
]


def install_kubeflow(
    installation_option,  deployment_option, cluster_name, aws_telemetry=True
):
    print(cluster_name)
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
        f"You are installing kubeflow {deployment_option} deployment with {installation_option}"
    )

    for component in Install_Sequence:
        build_component(
            installation_option,
            deployment_option,
            component,
            path_dic,
            cluster_name,
        )

    if aws_telemetry == True:
        build_component(
            installation_option,
            deployment_option,
            "aws-telemetry",
            path_dic,
            cluster_name,
        )


def build_component(
    installation_option,
    deployment_option,
    component_name,
    path_dic,
    cluster_name,
    crd_meet=True,
    namespace=None,
):
    print(f"==========Installing {component_name}==========")
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
            # cert-manager official chart command call
            if component_name == "cert-manager":
                build_retcode = build_certmanager()
                assert build_retcode == 0
            elif component_name == "aws-load-balancer-controller":
                build_retcode = build_alb_controller(cluster_name)
                assert build_retcode == 0
            ##deal with namespace already exist issue for rds-s3 auto set-up script
            elif component_name == "kubeflow-namespace":
                for kustomize_path in path_dic[component_name]["installation_options"]["kustomize"]:
                    apply_kustomize(kustomize_path)
            elif component_name == "ack-sagemaker-controller":
                build_ack_controller()
            else:
                install_helm(component_name, installation_path, namespace)
        # kustomize
        else:
            if "crd_required" in path_dic[component_name]:
                crd_required = path_dic[component_name]["crd_required"]
                crd_meet = False
            for kustomize_path in installation_path:
                if not crd_meet:
                    apply_kustomize(kustomize_path, crd_required)
                    crd_meet = True
                apply_kustomize(kustomize_path)
            
            #TO DO: Debug and add additional validation step for cert-manager resources in future for kubeflow-issuer to be installed
            #temporary solution to wait for 30s
            if component_name == "cert-manager":
                print("wait for 30s for cert-manager-webhook resource to be ready...")
                time.sleep(30)
        
        if "validations" in path_dic[component_name]:
            validate_component_installation(path_dic, component_name)
        print(f"All {component_name} pods are running!")
   
@retry (stop_max_attempt_number=3, wait_fixed=15000)
def validate_component_installation(path_dic,component_name):
    identifier = path_dic[component_name]["validations"]["identifier"]
    common_label = path_dic[component_name]["validations"]["common_label"]
    namespace = path_dic[component_name]["validations"]["namespace"]
    print(f"Waiting for {component_name} pods to be ready ...")
    retcode = kubectl_wait_pods(common_label, namespace, identifier)
    assert retcode == 0


def build_certmanager():
    retcode = subprocess.call(
        f"helm repo add jetstack https://charts.jetstack.io".split()
    )
    assert retcode == 0
    retcode = subprocess.call(f"helm repo update".split())
    assert retcode == 0
    cmd = f"helm install cert-manager jetstack/cert-manager \
                        --namespace cert-manager \
                        --create-namespace \
                        --version v1.5.0 \
                        --set installCRDs=true".split()
    return subprocess.call(cmd)


def build_alb_controller(cluster_name):
    retcode = subprocess.call(
        f"helm repo add eks https://aws.github.io/eks-charts".split()
    )
    assert retcode == 0
    retcode = subprocess.call(f"helm repo update".split())
    assert retcode == 0
    cmd = f"helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
            -n kube-system \
            --set clusterName={cluster_name} \
            --set serviceAccount.create=false \
            --set serviceAccount.name=aws-load-balancer-controller \
            --version v1.4.3".split()
    return subprocess.call(cmd)

def build_ack_controller():
    SERVICE="sagemaker"
    RELEASE_VERSION="v0.4.4"
    CHART_EXPORT_PATH="../../charts/common/ack-controller/sagemaker-chart"
    CHART_REF=f"{SERVICE}-chart"
    CHART_REPO=f"public.ecr.aws/aws-controllers-k8s/{CHART_REF}"
    CHART_PACKAGE=f"{CHART_REF}-{RELEASE_VERSION}.tgz"
    ACK_K8S_NAMESPACE="ack-system"
    PARAMS_PATH="../../awsconfigs/common/ack-sagemaker-controller/params.env"
    IAM_ROLE_ARN_FOR_IRSA=get_variable_from_params(PARAMS_PATH, "ACK_SAGEMAKER_OIDC_ROLE")
    ACK_AWS_REGION=get_variable_from_params(PARAMS_PATH, "ACK_AWS_REGION")
    LABEL_STRING='rbac.authorization.kubeflow.org/aggregate-to-kubeflow-edit: "true"'
    
    exec_shell(f"mkdir -p {CHART_EXPORT_PATH}")
    exec_shell(f"helm pull oci://{CHART_REPO} --version {RELEASE_VERSION} -d {CHART_EXPORT_PATH}")
    exec_shell(f"tar xvf {CHART_EXPORT_PATH}/{CHART_PACKAGE} -C {CHART_EXPORT_PATH}")
    exec_shell(f"yq e .aws.region=\"{ACK_AWS_REGION}\" -i {CHART_EXPORT_PATH}/{SERVICE}-chart/values.yaml")
    exec_shell(f"yq e .serviceAccount.annotations.\"eks.amazonaws.com/role-arn\"=\"{IAM_ROLE_ARN_FOR_IRSA}\" " +
        f"-i {CHART_EXPORT_PATH}/{SERVICE}-chart/values.yaml")
    find_and_replace_in_file(f"{CHART_EXPORT_PATH}/{SERVICE}-chart/templates/cluster-role-controller.yaml",
        "metadata:", f"metadata:\n  labels:\n    {LABEL_STRING}")
    exec_shell(f"helm install -n {ACK_K8S_NAMESPACE} --create-namespace ack-{SERVICE}-controller "
        f"{CHART_EXPORT_PATH}/{SERVICE}-chart")

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
        choices=['vanilla','cognito','rds-s3','rds-only','s3-only','cognito-rds-s3'],
        help=f"Kubeflow deployment options default is set to {DEPLOYMENT_OPTION_DEFAULT}",
        required=False,
    )
    
    parser.add_argument(
        "--cluster_name",
        type=str,
        help=f"EKS cluster Name",
        required=True,
    )

    args, _ = parser.parse_known_args()
    
    install_kubeflow(
        args.installation_option,  args.deployment_option, args.cluster_name, args.aws_telemetry
    )
