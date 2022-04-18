import argparse
from time import sleep
import boto3

from utils import (
    get_rds_client,
    get_s3_client,
    get_secrets_manager_client,
    load_yaml_file,
)


def main():
    metadata = load_yaml_file("utils/auto-rds-s3-setup-metadata.yaml")
    secrets_manager_client = get_secrets_manager_client(CLUSTER_REGION)
    delete_s3_bucket(metadata, secrets_manager_client)
    delete_rds(metadata, secrets_manager_client)


def delete_s3_bucket(metadata, secrets_manager_client):
    s3_client = get_s3_client(CLUSTER_REGION)
    s3_resource = boto3.resource("s3")
    bucket_name = metadata["S3"]["bucket"]

    print("Deleting S3 bucket...")

    bucket = s3_resource.Bucket(bucket_name)
    bucket.objects.all().delete()
    s3_client.delete_bucket(Bucket=bucket_name)

    secrets_manager_client.delete_secret(
        SecretId=metadata["S3"]["secretName"], ForceDeleteWithoutRecovery=True
    )


def delete_rds(metadata, secrets_manager_client):
    rds_client = get_rds_client(CLUSTER_REGION)
    db_instance_name = metadata["RDS"]["instanceName"]
    db_subnet_group_name = metadata["RDS"]["subnetGroupName"]

    print("Deleting RDS instance...")

    rds_client.modify_db_instance(
        DBInstanceIdentifier=db_instance_name,
        DeletionProtection=False,
        ApplyImmediately=True,
    )
    rds_client.delete_db_instance(
        DBInstanceIdentifier=db_instance_name, SkipFinalSnapshot=True
    )
    wait_periods = 30
    period_length = 30
    for _ in range(wait_periods):
        try:
            if (
                rds_client.describe_db_instances(DBInstanceIdentifier=db_instance_name)
                is not None
            ):
                sleep(period_length)
        except:
            print("RDS instance has been successfully deleted")
            break

    print("Deleting DB Subnet Group...")

    rds_client.delete_db_subnet_group(DBSubnetGroupName=db_subnet_group_name)
    print("DB Subnet Group has been successfully deleted")

    secrets_manager_client.delete_secret(
        SecretId=metadata["RDS"]["secretName"], ForceDeleteWithoutRecovery=True
    )


parser = argparse.ArgumentParser()
parser.add_argument(
    "--region",
    type=str,
    metavar="CLUSTER_REGION",
    help="Your cluster region code (eg: us-east-2)",
    required=True,
)
args, _ = parser.parse_known_args()

if __name__ == "__main__":
    CLUSTER_REGION = args.region
    main()
