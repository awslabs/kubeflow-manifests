import subprocess


SUBSTITUTION_VALUES = {
    "aws_authservice_path": {
        "LOGOUT_URL": "https://auth.platform.test.people.aws.dev/logout?client_id=testClientID1234567890&logout_uri=https://kubeflow.platform.test.people.aws.dev"
    },
    "aws_alb_ingress_controller_path": {"clusterName": "unit-test-cluster"},
    "pipelines_path": {
        "dbHost": "rm12abc4krxxxxx.xxxxxxxxxxxx.us-west-2.rds.amazonaws.com",
        "mlmdDb": "test-db",
        "bucketName": "unit-test-bucket",
        "minioServiceHost": "s3.amazonaws.com",
        "minioServiceRegion": "us-west-2",
    },
    "istio_ingress_base_path": {"loadBalancerScheme": "internet-facing"},
    "istio_ingress_overlay_path": {
        "CognitoUserPoolArn": "arn:aws:cognito-idp:us-west-2:123456789:userpool/us-west-2_3MiwqOkHU",
        "CognitoAppClientId": "1234567890abcdef",
        "CognitoUserPoolDomain": "auth.platform.example.com",
        "certArn": "arn:aws:acm:us-west-2:012345678912:certificate/9777e8d1-105e-4886-b42a-f35b67167fb5",
    },
}


def substitute_params():
    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"])
    repo_root = repo_root.decode()
    repo_root = repo_root.strip()
    aws_configs_path = f"{repo_root}/awsconfigs"
    env_file_paths = {
        "pipelines_path": f"{aws_configs_path}/apps/pipeline/params.env",
        "aws_authservice_path": f"{aws_configs_path}/common/aws-authservice/base/params.env",
        "aws_alb_ingress_controller_path": f"{aws_configs_path}/common/aws-alb-ingress-controller/params.env",
        "istio_ingress_base_path": f"{aws_configs_path}/common/istio-ingress/base/params.env",
        "istio_ingress_overlay_path": f"{aws_configs_path}/common/istio-ingress/overlays/params.env",
    }
    for env_file in env_file_paths:
        with open(env_file_paths[env_file], "w") as file:
            for key, value in SUBSTITUTION_VALUES[env_file].items():
                file.write(f"{key}={value}\n")
    return


substitute_params()
