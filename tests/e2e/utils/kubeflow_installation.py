from pickle import FALSE
from e2e.utils.utils import load_yaml_file, print_banner
import argparse
from e2e.utils.utils import (
    kubectl_wait_pods,
    apply_kustomize,
    install_helm,
)
import subprocess
import os

INSTALLATION_PATH_FILE_VANILLA = "./resources/installation_config/vanilla.yaml"
INSTALLATION_PATH_FILE_COGNITO = "./resources/installation_config/cognito.yaml"

Install_Sequence = [
    "cert-manager",
    "kubeflow-roles",
    "kubeflow-issuer",
    "istio-1-14",
    "kubeflow-namespace",
    "dex",
    "cluster-local-gateway",
    "knative-serving",
    "knative-eventing",
    "oidc-authservice",
    "kubeflow-istio-resources",
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
    #"ack-sagemaker-controller",
    "ingress",
    "aws-load-balancer-controller",
    "aws-authservice",
]


def install_kubeflow(
    installation_option, aws_telemetry_option, deployment_option, cluster_name
):
    INSTALLATION_OPTION = installation_option
    AWS_TELEMETRY_OPTION = aws_telemetry_option
    DEPLOYMENT_OPTION = deployment_option

    if DEPLOYMENT_OPTION == "vanilla":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_VANILLA)
    elif DEPLOYMENT_OPTION == "cognito":
        path_dic = load_yaml_file(INSTALLATION_PATH_FILE_COGNITO)

    print_banner(
        f"You are installing kubeflow {DEPLOYMENT_OPTION} deployment with {INSTALLATION_OPTION}"
    )

    for component in Install_Sequence:
        build_component(
            INSTALLATION_OPTION,
            DEPLOYMENT_OPTION,
            component,
            path_dic,
            cluster_name,
        )

    if AWS_TELEMETRY_OPTION == "enable":
        build_component(
            INSTALLATION_OPTION,
            DEPLOYMENT_OPTION,
            "aws-telemetry",
            path_dic,
            cluster_name,
        )


def build_component(
    INSTALLATION_OPTION,
    DEPLOYMENT_OPTION,
    component_name,
    path_dic,
    cluster_name,
    crd_meet=True,
    namespace=None,
):
    print(f"==========Installing {component_name}==========")
    if component_name not in path_dic:
        print(
            f"component {component_name} is not applicable for deployment option: {DEPLOYMENT_OPTION}"
        )
        return
    else:
        installation_path = path_dic[component_name]["installation_options"][
            INSTALLATION_OPTION
        ]

        if INSTALLATION_OPTION == "helm":
            # cert-manager official chart command call
            if component_name == "cert-manager":
                build_retcode = build_certmanager()
                assert build_retcode == 0
            elif component_name == "aws-load-balancer-controller":
                build_retcode = build_alb_controller(cluster_name)
                assert build_retcode == 0
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

    if "validations" in path_dic[component_name]:
        identifier = path_dic[component_name]["validations"]["identifier"]
        common_label = path_dic[component_name]["validations"]["common_label"]
        namespace = path_dic[component_name]["validations"]["namespace"]
        print(f"Waiting for {component_name} pods to be ready ...")
        retcode = kubectl_wait_pods(common_label, namespace, identifier)
        assert retcode == 0
    print(f"All {component_name} pods are running!")


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
                        --version v1.9.1 \
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
            --version v2.4.3".split()
    return subprocess.call(cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    INSTALLATION_OPTION_DEFAULT = "kustomize"
    parser.add_argument(
        "--installation_option",
        type=str,
        default=INSTALLATION_OPTION_DEFAULT,
        help=f"Kubeflow Installation option (helm/kustomize), default is set to {INSTALLATION_OPTION_DEFAULT}",
        required=False,
    )
    AWS_TELEMETRY_DEFAULT = "enable"
    parser.add_argument(
        "--aws_telemetry_option",
        type=str,
        default=AWS_TELEMETRY_DEFAULT,
        help=f"Usage tracking (enable/disable), default is set to {AWS_TELEMETRY_DEFAULT}",
        required=False,
    )
    DEPLOYMENT_OPTION_DEFAULT = "vanilla"
    parser.add_argument(
        "--deployment_option",
        type=str,
        default=DEPLOYMENT_OPTION_DEFAULT,
        help=f"Kubeflow deployment options (vanilla/cognito/rds_and_s3/rds_only/s3_only/cognito-rds-s3), default is set to {DEPLOYMENT_OPTION_DEFAULT}",
        required=False,
    )

    args, _ = parser.parse_known_args()
    INSTALLATION_OPTION = args.installation_option
    AWS_TELEMETRY_OPTION = args.aws_telemetry_option
    DEPLOYMENT_OPTION = args.deployment_option
    CLUSTER_NAME = os.environ["CLUSTER_NAME"]
    install_kubeflow(
        INSTALLATION_OPTION, AWS_TELEMETRY_OPTION, DEPLOYMENT_OPTION, CLUSTER_NAME
    )
