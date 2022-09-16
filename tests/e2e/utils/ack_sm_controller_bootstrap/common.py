# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import yaml
import logging

logger = logging.getLogger(__name__)

CONFIG_FILE_PATH = "./utils/ack_sm_controller_bootstrap/config.yaml"
OUTPUT_FILE_PATH = "../../awsconfigs/common/ack-sagemaker-controller/params.env"

ACK_OIDC_ROLE_NAME_PREFIX = "kf-ack-sm-controller-role"
SM_STUDIO_POLICY_NAME_PREFIX = "sm-studio-full-access"