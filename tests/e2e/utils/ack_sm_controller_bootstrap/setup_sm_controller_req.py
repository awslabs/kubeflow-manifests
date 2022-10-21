# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import json
import boto3

from e2e.utils.utils import (
    load_json_file,
    get_iam_client,
    get_eks_client,
)
from e2e.fixtures.cluster import (
    associate_iam_oidc_provider,
)
from e2e.utils.aws.iam import IAMPolicy
from e2e.utils.ack_sm_controller_bootstrap import common
from e2e.utils.config import configure_env_file
from e2e.utils.utils import print_banner, load_yaml_file, write_env_to_yaml


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def profile_trust_policy(
    cluster, region, account_id
):
    eks_client = get_eks_client(region=region)

    resp = eks_client.describe_cluster(name=cluster)
    oidc_url = resp["cluster"]["identity"]["oidc"]["issuer"].split("https://")[1]

    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": f"arn:aws:iam::{account_id}:oidc-provider/{oidc_url}"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{oidc_url}:aud": "sts.amazonaws.com",
                        f"{oidc_url}:sub": [ 
                            "system:serviceaccount:ack-system:ack-sagemaker-controller",
                            "system:serviceaccount:ack-system:ack-applicationautoscaling-controller"
                        ]
                    }
                },
            }
        ],
    }
    return json.dumps(trust_policy)

def create_ack_oidc_role(cluster_name, region):
    iam_client = get_iam_client(region=region)
    acc_id = get_account_id()
    role_name = f"{common.ACK_OIDC_ROLE_NAME_PREFIX}-{cluster_name}"
    policy_name = f"{common.SM_STUDIO_POLICY_NAME_PREFIX}-{cluster_name}"

    resp = iam_client.create_role(
        RoleName=role_name, AssumeRolePolicyDocument=profile_trust_policy(cluster_name, region, acc_id)
    )
    oidc_role_arn = resp["Role"]["Arn"]

    print(f"Created IAM Role : {oidc_role_arn}")

    iam_client.attach_role_policy(
        RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
    )
    policy = IAMPolicy(name=policy_name, region=region)
    policy.create(
        policy_document=load_json_file(
            "../../awsconfigs/infra_configs/iam_ack_oidc_sm_studio_policy.json"
        )
    )
    custom_policy_arn = f"arn:aws:iam::{acc_id}:policy/{policy_name}"
    iam_client.attach_role_policy(
        RoleName=role_name, PolicyArn=custom_policy_arn
    )


def get_role_arn(role_name, region):
    iam_client = get_iam_client(region=region)
    resp = iam_client.get_role(RoleName=role_name)
    oidc_role_arn = resp["Role"]["Arn"]
    return oidc_role_arn

def get_account_id():
    return boto3.client("sts").get_caller_identity().get("Account")

def write_params(oidc_role_arn, region, env_file_path, config_file_path):
    output_dict = {
        "ACK_SAGEMAKER_OIDC_ROLE": oidc_role_arn,
        "ACK_AWS_REGION": region
    }
    configure_env_file(env_file_path, output_dict)
    print(f"Params file written to : {env_file_path}")

    write_env_to_yaml({"ack_sagemaker_oidc_role": oidc_role_arn}, config_file_path)
    print(f"Config file written to : {config_file_path}")

if __name__ == "__main__":
    print_banner("Reading Config")
    config_file_path = common.CONFIG_FILE_PATH
    cfg = load_yaml_file(file_path=config_file_path)
    cluster_region = cfg["cluster"]["region"]
    cluster_name = cfg["cluster"]["name"]
    
    print_banner("Create OIDC IAM role for ACK SageMaker Controller")
    try:
        create_ack_oidc_role(cluster_name, cluster_region)
    except Exception as e:
        print(e)
        print("Try running cleanup_sm_controller_req.py")
    
    ack_oidc_role_name = f"{common.ACK_OIDC_ROLE_NAME_PREFIX}-{cluster_name}"
    oidc_role_arn = get_role_arn(ack_oidc_role_name, cluster_region)

    print_banner("Writing params.env for ACK SageMaker Controller")
    output_params_file_path = common.OUTPUT_FILE_PATH
    write_params(oidc_role_arn, cluster_region, output_params_file_path, config_file_path)

    print_banner("SUCCESS")


