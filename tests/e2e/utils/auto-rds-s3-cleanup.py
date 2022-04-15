import argparse
from time import sleep
import boto3

from utils import get_rds_client, get_s3_client, get_secrets_manager_client


def main():
    metadata_dict = {}
    with open("auto-rds-s3-setup-metadata", "r") as setup_metadata:
        for line in setup_metadata.readlines():
            metadata = line.split("=")
            metadata_dict[metadata[0]] = metadata[1].strip("\n")
    secrets_manager_client = get_secrets_manager_client(CLUSTER_REGION)
    delete_s3_bucket(metadata_dict, secrets_manager_client)
    delete_rds(metadata_dict, secrets_manager_client)


def delete_s3_bucket(metadata_dict, secrets_manager_client):
    s3_client = get_s3_client(CLUSTER_REGION)
    s3_resource = boto3.resource("s3")
    bucket_name = metadata_dict["bucket_name"]

    print("Deleting S3 bucket...")

    bucket = s3_resource.Bucket(bucket_name)
    bucket.objects.all().delete()
    s3_client.delete_bucket(Bucket=bucket_name)

    buckets = s3_client.list_buckets()["Buckets"]
    assert any(bucket["Name"] == bucket_name for bucket in buckets) is False
    print("S3 bucket has been successfully deleted")

    secrets_manager_client.delete_secret(
        SecretId=metadata_dict["s3_secret_name"], ForceDeleteWithoutRecovery=True
    )


def delete_rds(metadata_dict, secrets_manager_client):
    rds_client = get_rds_client(CLUSTER_REGION)
    db_instance_name = metadata_dict["db_instance_name"]
    db_subnet_group_name = metadata_dict["db_subnet_group_name"]

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
        SecretId=metadata_dict["rds_secret_name"], ForceDeleteWithoutRecovery=True
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
