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
from e2e.utils.pipelines import common
from e2e.utils.config import configure_env_file
from e2e.utils.utils import print_banner, load_yaml_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_account_id():
    return boto3.client("sts").get_caller_identity().get("Account")

def delete_iam_role(role_name, region):
    iam_client = get_iam_client(region=region)
    try:
        iam_client.detach_role_policy(
            RoleName=role_name, PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
        )
    except:
        logger.log("Failed to detach role policy, it may not exist anymore.")
    
    iam_client.delete_role(RoleName=role_name)
    print(f"Deleted IAM Role : {role_name}")


if __name__ == "__main__":
    print_banner("Reading Config")
    config_file_path = common.CONFIG_FILE_PATH
    cfg = load_yaml_file(file_path=config_file_path)
    cluster_region = cfg["cluster"]["region"]
    cluster_name = cfg["cluster"]["name"]

    print_banner("Deleting all resources created for Pipeline IRSA")
    role_name = f"{common.PIPELINE_OIDC_ROLE_NAME_PREFIX}-{cluster_name}"
    delete_iam_role(role_name, cluster_region)

    print_banner("CLEANUP SUCCESSFUL")

