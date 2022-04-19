import argparse
from time import sleep
import boto3
from e2e.fixtures.cluster import delete_iam_service_account

from e2e.utils.utils import (
    get_rds_client,
    get_s3_client,
    get_secrets_manager_client,
    load_yaml_file,
    kubectl_delete,
)


def main():
    metadata = load_yaml_file("utils/rds-s3/metadata.yaml")
    secrets_manager_client = get_secrets_manager_client(CLUSTER_REGION)
    delete_s3_bucket(metadata, secrets_manager_client)
    delete_rds(metadata, secrets_manager_client)
    uninstall_secrets_manager()


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


def uninstall_secrets_manager():
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretproviderclass.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/csidriver.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store-csi-driver.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretprovidersyncing.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml"
    )
    print("Secrets Manager Driver successfully deleted")

    delete_iam_service_account(
        service_account_name="kubeflow-secrets-manager-sa",
        namespace="kubeflow",
        cluster_name=CLUSTER_NAME,
        region=CLUSTER_REGION,
    )
    print("IAM service account kubeflow-secrets-manager-sa successfully deleted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--region",
        type=str,
        metavar="CLUSTER_REGION",
        help="Your cluster region code (eg: us-east-2)",
        required=True,
    )
    parser.add_argument(
        "--cluster",
        type=str,
        metavar="CLUSTER_NAME",
        help="Your cluster name (eg: mycluster-1)",
        required=True,
    )
    args, _ = parser.parse_known_args()

    CLUSTER_REGION = args.region
    CLUSTER_NAME = args.cluster

    main()
