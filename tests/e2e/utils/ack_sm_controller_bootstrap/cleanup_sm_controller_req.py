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
from e2e.utils.utils import print_banner, load_yaml_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_account_id():
    return boto3.client("sts").get_caller_identity().get("Account")

def delete_iam_role(role_name, policy_name, region):
    iam_client = get_iam_client(region=region)
    try:
        iam_client.detach_role_policy(
            RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
        )
        acc_id = get_account_id()
        custom_policy_arn = f"arn:aws:iam::{acc_id}:policy/{policy_name}"
        iam_client.detach_role_policy(
            RoleName=role_name, PolicyArn=custom_policy_arn
        ) 
    except:
        logger.log("Failed to detach role policy, it may not exist anymore.")
    
    iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM Role : {role_name}")

def delete_iam_policy(policy_name, region):
    acc_id = get_account_id()
    custom_policy_arn = f"arn:aws:iam::{acc_id}:policy/{policy_name}"
    iam_client = get_iam_client(region=region)
    iam_client.delete_policy(PolicyArn=custom_policy_arn)
    print(f"Deleted IAM Policy : {policy_name}")

if __name__ == "__main__":
    print_banner("Reading Config")
    config_file_path = common.CONFIG_FILE_PATH
    cfg = load_yaml_file(file_path=config_file_path)
    cluster_region = cfg["cluster"]["region"]
    cluster_name = cfg["cluster"]["name"]

    print_banner("Deleting all resources created for ACK SageMaker Controller")
    role_name = f"{common.ACK_OIDC_ROLE_NAME_PREFIX}-{cluster_name}"
    policy_name = f"{common.SM_STUDIO_POLICY_NAME_PREFIX}-{cluster_name}"
    delete_iam_role(role_name, policy_name, cluster_region)
    delete_iam_policy(policy_name, cluster_region)

    print_banner("CLEANUP SUCCESSFUL")


