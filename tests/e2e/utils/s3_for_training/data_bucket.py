# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import sys, os, subprocess

import json
import boto3
import logging
import time

from botocore.exceptions import ClientError
from typing import Any

from e2e.utils.utils import wait_for

logger = logging.getLogger(__name__)

def delete_s3_bucket(bucket_name, s3_client):
    s3_resource = boto3.resource("s3")

    bucket = s3_resource.Bucket(bucket_name)
    logger.info(f"deleting s3 bucket {bucket_name}")
    bucket.objects.all().delete()
    s3_client.delete_bucket(Bucket=bucket_name)


class S3BucketWithTrainingData:
    """
    Encapsulates S3BucketWithTrainingData functions.
    """

    def __init__(
        self,
        name: str = None,
        region: str = "us-east-1",
        s3_client: Any = None,
        arn: str = None,
    ):
        self.region = region
        self.s3_client = s3_client or boto3.client("s3", region_name=region)
        self.name = name
        self.arn = arn
        if not name and not arn:
            raise ValueError("Either role name or arn should be defined")

    def create(self):
        try:
            print(f"Bucket being created: {self.name}")
            # TODO: the test is currently configured only for us-east-1. The cluster can be in any region though.
            self.s3_client.create_bucket(
                Bucket=self.name,
                # CreateBucketConfiguration={"LocationConstraint": self.region},
            )
            time.sleep(60)

            cmd = f"python utils/s3_for_training/sync.py {self.name} {self.region}".split()
            subprocess.Popen(cmd)
            time.sleep(120)

        except ClientError:
            logger.exception(f"failed to create S3 bucket {self.name}")
            raise
        else:
            logger.info(f"created s3 bucket {self.name}.")
            return self.name

    def delete(self):
        try:
            delete_s3_bucket(self.name, self.s3_client)
            logger.info(f"deleted s3 bucket {self.name}")
        except ClientError:
            logger.exception(f"failed to delete s3 bucket {self.name}")
            raise