# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE = "./utils/cognito_bootstrap/config.yaml"

# For creating an alias record to other AWS resource, route53 needs hosted zone id and DNS name.
# Since CloudFront is a global service, there is only one hosted zone id
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-aliastarget.html
CLOUDFRONT_HOSTED_ZONE_ID = "Z2FDTNDATAQYW2"

# TODO: Remove this methods from this file and move it to the utils file
def load_cfg(file_path: str = CONFIG_FILE):
    with open(file_path, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def write_cfg(config: dict, file_path: str = CONFIG_FILE):
    with open(file_path, "w") as stream:
        yaml.safe_dump(config, stream)


def print_banner(step_name: str):
    logger.info("-" * 88)
    logger.info(step_name)
    logger.info("-" * 88)
