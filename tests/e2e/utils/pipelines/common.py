# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = "./utils/pipelines/config.yaml"
OUTPUT_FILE_PATH = "../../awsconfigs/apps/pipeline/s3/service-account.yaml"

PIPELINE_OIDC_ROLE_NAME_PREFIX = "kf-pipeline-role"
