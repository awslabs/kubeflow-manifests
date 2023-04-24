import argparse
from time import sleep
import boto3, botocore
from e2e.fixtures.cluster import delete_iam_service_account

from e2e.utils.utils import (
    get_rds_client,
    get_s3_client,
    get_secrets_manager_client,
    get_iam_client,
    load_yaml_file,
    kubectl_delete,
)


def main():
    metadata = load_yaml_file("utils/rds-s3/metadata.yaml")
    region = metadata["CLUSTER"]["region"]
    cluster_name = metadata["CLUSTER"]["name"]
    secrets_manager_client = get_secrets_manager_client(region)
    delete_s3_bucket(metadata, secrets_manager_client, region)
    delete_rds(metadata, secrets_manager_client, region)
    uninstall_secrets_manager(region, cluster_name)
    if "backEndRoleArn" in metadata["S3"]:
        delete_pipeline_iam_role(metadata, region)


def delete_s3_bucket(metadata, secrets_manager_client, region):
    s3_client = get_s3_client(region)
    s3_resource = boto3.resource("s3")
    bucket_name = metadata["S3"]["bucket"]

    if check_bucket(bucket_name, s3_client):
        bucket = s3_resource.Bucket(bucket_name)
        print("Deleting S3 bucket...")
        bucket.objects.all().delete()
        s3_client.delete_bucket(Bucket=bucket_name)
    else:
        print("Skip deleting S3 bucket...")

    if metadata["S3"]["secretName"]:
        secrets_manager_client.delete_secret(
            SecretId=metadata["S3"]["secretName"], ForceDeleteWithoutRecovery=True
        )


def check_bucket(bucket_name, s3_client):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print("Bucket Exists!")
        return True
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = int(e.response["Error"]["Code"])
        if error_code == 403:
            print("Private Bucket. Forbidden Access!")
            return True
        elif error_code == 404:
            print("Bucket Does Not Exist!")
            return False


def delete_rds(metadata, secrets_manager_client, region):
    rds_client = get_rds_client(region)
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


def uninstall_secrets_manager(region, cluster_name):
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/rbac-secretproviderclass.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/csidriver.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/secrets-store-csi-driver.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.3.2/deploy/rbac-secretprovidersyncing.yaml"
    )
    kubectl_delete(
        "https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml"
    )
    print("Secrets Manager Driver successfully deleted")

    delete_iam_service_account(
        service_account_name="kubeflow-secrets-manager-sa",
        namespace="kubeflow",
        cluster_name=cluster_name,
        region=region,
    )
    print("IAM service account kubeflow-secrets-manager-sa successfully deleted")


def delete_pipeline_iam_role(metadata, region):
    iam_client = get_iam_client(region=region)
    pipeline_roles = []
    pipeline_roles.append(metadata["S3"]["backEndRoleArn"].split("/")[1])
    pipeline_roles.append(metadata["S3"]["profileRoleArn"].split("/")[1])
    policy_arn = metadata["S3"]["policyArn"]
    for role_name in pipeline_roles:
        try:
            iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        except:
            raise ("Failed to detach role policy, it may not exist anymore.")

        iam_client.delete_role(RoleName=role_name)
        print(f"Deleted IAM Role : {role_name}")

    iam_client.delete_policy(PolicyArn=policy_arn)
    print(f"Deleted IAM Policy : {policy_arn}")

if __name__ == "__main__":
    main()
