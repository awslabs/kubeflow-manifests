# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import boto3
import logging

from botocore.exceptions import ClientError
from typing import Any

logger = logging.getLogger(__name__)


class ElasticLoadBalancingV2:
    """
    Encapsulates ELBv2 functions.
    """

    def __init__(
        self, dns: str = None, region: str = "us-east-1", elbv2_client: Any = None
    ):
        self.dns = dns
        self.region = region
        self.elbv2_client = elbv2_client or boto3.client("elbv2", region_name=region)
        self.name = self.get_name_from_dns(dns)

    def describe(self) -> dict:
        try:
            response = self.elbv2_client.describe_load_balancers(
                Names=[
                    self.name,
                ]
            )
        except ClientError:
            logger.exception(f"Failed to describe load balancer {self.name}")
        else:
            return response["LoadBalancers"][0]

    def get_name_from_dns(self, dns: str):
        """
        Workaround to extract load balancer name from dns.

        If ALB DNS is 72d70454-istiosystem-istio-2ab2-xxxxxxxxxx.us-east-1.elb.amazonaws.com
        ALB name is 72d70454-istiosystem-istio-2ab2
        """
        dns_prefix = dns.split(".")[0]
        last_hypen_index = dns_prefix.rfind("-")
        if last_hypen_index != -1:
            return dns[:last_hypen_index]
        else:
            return dns_prefix

    def get_registered_target_groups(self, alb_arn: str) -> dict:
        try:
            response = self.elbv2_client.describe_target_groups(LoadBalancerArn=alb_arn)
        except ClientError:
            logger.exception(
                f"Failed to get registered target groups for load balancer {self.name}"
            )
        else:
            return response["TargetGroups"]

    def delete_registered_target_groups(self, target_groups):
        for target_group in target_groups:
            target_group_arn = target_group["TargetGroupArn"]
            try:
                self.elbv2_client.delete_target_group(
                    TargetGroupArn=target_group_arn,
                )
                logger.info(f"deleted target group {target_group_arn}")
            except ClientError:
                logger.exception(f"failed to delete target group {target_group_arn}")
                pass

    def get_listeners(self, alb_arn: str) -> dict:
        try:
            response = self.elbv2_client.describe_listeners(LoadBalancerArn=alb_arn)
        except ClientError:
            logger.exception(f"Failed to get listeners for load balancer {self.name}")
        else:
            return response["Listeners"]

    def delete_listeners(self, listeners):
        for listener in listeners:
            listener_arn = listener["ListenerArn"]
            try:
                self.elbv2_client.delete_listener(
                    ListenerArn=listener_arn,
                )
                logger.info(f"deleted listener {listener_arn}")
            except ClientError:
                logger.exception(f"failed to delete listener {listener_arn}")
                pass

    def delete(self):
        alb_arn = self.describe()["LoadBalancerArn"]

        listeners = self.get_listeners(alb_arn=alb_arn)
        target_groups = self.get_registered_target_groups(alb_arn=alb_arn)

        self.delete_listeners(listeners=listeners)
        try:
            self.elbv2_client.delete_load_balancer(LoadBalancerArn=alb_arn)
            logger.info(f"deleted load balancer {self.name}")
        except ClientError:
            logger.exception(f"Failed to delete load balancer {self.name}")

        self.delete_registered_target_groups(target_groups=target_groups)
