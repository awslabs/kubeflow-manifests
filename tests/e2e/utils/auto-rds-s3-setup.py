import argparse
import boto3
import subprocess
import json

from importlib_metadata import metadata
from utils import (
    get_ec2_client,
    get_iam_client,
    get_rds_client,
    get_eks_client,
    get_s3_client,
    get_secrets_manager_client,
    kubectl_apply,
)

from shutil import which
from time import sleep


def main():
    header()

    verify_prerequisites()
    s3_client = get_s3_client(
        region=CLUSTER_REGION,
        access_key_id=S3_ACCESS_KEY_ID,
        secret_access_key_id=S3_SECRET_ACCESS_KEY,
    )
    secrets_manager_client = get_secrets_manager_client(CLUSTER_REGION)
    setup_s3(s3_client, secrets_manager_client)
    rds_client = get_rds_client(CLUSTER_REGION)
    eks_client = get_eks_client(CLUSTER_REGION)
    ec2_client = get_ec2_client(CLUSTER_REGION)
    setup_rds(rds_client, secrets_manager_client, eks_client, ec2_client)
    setup_cluster_secrets()
    setup_kubeflow()

    footer()
    script_metadata = [f"bucket_name={S3_BUCKET_NAME}", f"db_instance_name={DB_INSTANCE_NAME}",
                       f"db_subnet_group_name={DB_SUBNET_GROUP_NAME}"]
    script_metadata = [metadata + '\n' for metadata in script_metadata]

    with open("auto-rds-s3-setup-metadata", "w") as setup_metadata:
        setup_metadata.writelines(script_metadata)


def header():
    print("=================================================================")
    print("                         RDS S3 Setup")


def verify_prerequisites():
    print("=================================================================")
    print("                   Prerequisites Verification")
    print("=================================================================")

    verify_oidc_provider_prerequisite()
    verify_eksctl_is_installed()
    verify_kubectl_is_installed()


def verify_oidc_provider_prerequisite():
    print("Verifying OIDC provider...")

    if is_oidc_provider_present():
        print("OIDC provider found")
    else:
        raise Exception(
            f"Prerequisite not met : No OIDC provider found for cluster '{CLUSTER_NAME}'!"
        )


def is_oidc_provider_present() -> bool:
    iam_client = get_iam_client(CLUSTER_REGION)
    oidc_providers = iam_client.list_open_id_connect_providers()[
        "OpenIDConnectProviderList"
    ]

    if len(oidc_providers) == 0:
        return False

    for oidc_provider in oidc_providers:
        oidc_provider_tags = iam_client.get_open_id_connect_provider(
            OpenIDConnectProviderArn=oidc_provider["Arn"]
        )["Tags"]

        if any(
            tag["Key"] == "alpha.eksctl.io/cluster-name"
            and tag["Value"] == CLUSTER_NAME
            for tag in oidc_provider_tags
        ):
            return True

    return False


def verify_eksctl_is_installed():
    print("Verifying eksctl is installed...")

    is_prerequisite_met = which("eksctl") is not None

    if is_prerequisite_met:
        print("eksctl found!")
    else:
        raise Exception(
            "Prerequisite not met : eksctl could not be found, make sure it is installed or in your PATH!"
        )


def verify_kubectl_is_installed():
    print("Verifying kubectl is installed...")

    is_prerequisite_met = which("kubectl") is not None

    if is_prerequisite_met:
        print("kubectl found!")
    else:
        raise Exception(
            "Prerequisite not met : kubectl could not be found, make sure it is installed or in your PATH!"
        )


def setup_s3(s3_client, secrets_manager_client):
    print("=================================================================")
    print("                          S3 Setup")
    print("=================================================================")

    setup_s3_bucket(s3_client)
    setup_s3_secrets(secrets_manager_client)


def setup_s3_bucket(s3_client):
    if not does_bucket_exist(s3_client):
        create_s3_bucket(s3_client)
    else:
        print(
            f"Skipping S3 bucket creation, bucket '{S3_BUCKET_NAME}' already exists!")


def does_bucket_exist(s3_client):
    buckets = s3_client.list_buckets()["Buckets"]
    return any(bucket["Name"] == S3_BUCKET_NAME for bucket in buckets)


def create_s3_bucket(s3_client):
    print("Creating S3 bucket...")

    args = {"ACL": "private", "Bucket": S3_BUCKET_NAME}
    # CreateBucketConfiguration is necessary to provide LocationConstraint unless using default region of us-east-1
    if CLUSTER_REGION != "us-east-1":
        args["CreateBucketConfiguration"] = {
            "LocationConstraint": CLUSTER_REGION}

    s3_client.create_bucket(**args)
    print("S3 bucket created!")


def setup_s3_secrets(secrets_manager_client):
    s3_secret_name = "s3-secret"

    if not does_secret_already_exist(secrets_manager_client, s3_secret_name):
        create_s3_secret(secrets_manager_client, s3_secret_name)
    else:
        print(
            f"Skipping S3 secret creation, secret '{s3_secret_name}' already exists!")


def does_secret_already_exist(secrets_manager_client, secret_name):
    matching_secrets = secrets_manager_client.list_secrets(
        Filters=[{"Key": "name", "Values": [secret_name]}]
    )["SecretList"]

    return len(matching_secrets) > 0


def create_s3_secret(secrets_manager_client, s3_secret_name):
    print("Creating S3 secret...")

    secret_string = json.dumps(
        {"accesskey": f"{S3_ACCESS_KEY_ID}", "secretkey": f"{S3_SECRET_ACCESS_KEY}"}
    )

    secrets_manager_client.create_secret(
        Name=s3_secret_name,
        Description="Kubeflow S3 secret",
        SecretString=secret_string,
    )

    print("S3 secret created!")


def setup_rds(rds_client, secrets_manager_client, eks_client, ec2_client):
    print("=================================================================")
    print("                          RDS Setup")
    print("=================================================================")

    rds_secret_name = "rds-secreta"

    if not does_database_exist(rds_client):
        if not does_secret_already_exist(secrets_manager_client, rds_secret_name):
            db_root_password = setup_db_instance(
                rds_client, secrets_manager_client, eks_client, ec2_client
            )
            create_rds_secret(secrets_manager_client,
                              rds_secret_name, db_root_password)
        else:
            print(
                f"Skipping RDS setup, secret '{rds_secret_name}' already exists!")
    else:
        print(
            f"Skipping RDS setup, DB instance '{DB_INSTANCE_NAME}' already exists!")


def does_database_exist(rds_client):
    matching_databases = rds_client.describe_db_instances(
        Filters=[{"Name": "db-instance-id", "Values": [DB_INSTANCE_NAME]}]
    )["DBInstances"]

    return len(matching_databases) > 0


def setup_db_instance(rds_client, secrets_manager_client, eks_client, ec2_client):
    setup_db_subnet_group(rds_client, eks_client, ec2_client)
    return create_db_instance(
        rds_client, secrets_manager_client, eks_client, ec2_client
    )


def setup_db_subnet_group(rds_client, eks_client, ec2_client):
    if not does_db_subnet_group_exist(rds_client):
        create_db_subnet_group(rds_client, eks_client, ec2_client)
    else:
        print(
            f"Skipping DB subnet group creation, DB subnet group '{DB_SUBNET_GROUP_NAME}' already exists!"
        )


def does_db_subnet_group_exist(rds_client):
    try:
        rds_client.describe_db_subnet_groups(
            DBSubnetGroupName=DB_SUBNET_GROUP_NAME)
        return True
    except rds_client.exceptions.DBSubnetGroupNotFoundFault:
        return False


def create_db_subnet_group(rds_client, eks_client, ec2_client):
    print("Creating DB subnet group...")

    subnet_ids = get_cluster_private_subnet_ids(eks_client, ec2_client)

    rds_client.create_db_subnet_group(
        DBSubnetGroupName=DB_SUBNET_GROUP_NAME,
        DBSubnetGroupDescription="Subnet group for Kubeflow metadata db",
        SubnetIds=subnet_ids,
    )

    print("DB subnet group created!")


def get_cluster_private_subnet_ids(eks_client, ec2_client):
    subnet_ids = eks_client.describe_cluster(name=CLUSTER_NAME)["cluster"][
        "resourcesVpcConfig"
    ]["subnetIds"]

    subnets = ec2_client.describe_subnets(SubnetIds=subnet_ids)["Subnets"]
    private_subnets = []
    for subnet in subnets:
        for tags in subnet["Tags"]:
            if "SubnetPrivate" in tags["Value"]:
                private_subnets.append(subnet)

    def get_subnet_id(subnet):
        return subnet["SubnetId"]

    return list(map(get_subnet_id, private_subnets))


def create_db_instance(rds_client, secrets_manager_client, eks_client, ec2_client):
    print("Creating DB instance...")

    vpc_ids = get_cluster_vpc_ids(eks_client)
    vpc_security_group_id = get_vpc_security_group_id(vpc_ids, ec2_client)

    db_root_password = get_db_root_password_or_generate_one(
        secrets_manager_client)

    rds_client.create_db_instance(
        DBName=DB_NAME,
        DBInstanceIdentifier=DB_INSTANCE_NAME,
        AllocatedStorage=DB_INITIAL_STORAGE,
        DBInstanceClass=DB_INSTANCE_TYPE,
        Engine="mysql",
        MasterUsername=DB_ROOT_USER,
        MasterUserPassword=db_root_password,
        VpcSecurityGroupIds=[vpc_security_group_id],
        DBSubnetGroupName=DB_SUBNET_GROUP_NAME,
        BackupRetentionPeriod=DB_BACKUP_RETENTION_PERIOD,
        MultiAZ=True,
        PubliclyAccessible=False,
        StorageType=DB_STORAGE_TYPE,
        DeletionProtection=True,
        MaxAllocatedStorage=DB_MAX_STORAGE,
    )

    print("DB instance created!")

    wait_for_rds_db_instance_to_become_available(rds_client)

    return db_root_password


def get_db_root_password_or_generate_one(secrets_manager_client):
    if DB_ROOT_PASSWORD is None:
        return secrets_manager_client.get_random_password(
            PasswordLength=32,
            ExcludeNumbers=False,
            ExcludePunctuation=True,
            ExcludeUppercase=False,
            ExcludeLowercase=False,
            IncludeSpace=False,
        )["RandomPassword"]
    else:
        return DB_ROOT_PASSWORD


def get_cluster_vpc_ids(eks_client):
    vpcs = eks_client.describe_cluster(name=CLUSTER_NAME)["cluster"][
        "resourcesVpcConfig"
    ]["vpcId"]

    return vpcs


def get_vpc_security_group_id(vpc_id, ec2_client):

    security_groups = ec2_client.describe_security_groups(
        Filters=[
            {"Name": "tag:alpha.eksctl.io/cluster-name",
                "Values": [CLUSTER_NAME]},
            {"Name": "vpc-id", "Values": [vpc_id]},
            {
                "Name": "tag:aws:cloudformation:logical-id",
                "Values": ["ClusterSharedNodeSecurityGroup"],
            },
        ]
    )["SecurityGroups"]

    assert len(security_groups) > 0

    def get_security_group_id(security_group):
        return security_group["GroupId"]

    # Note : We only need to return 1 security group because we use the shared node security group, this fixes https://github.com/awslabs/kubeflow-manifests/issues/137
    return list(map(get_security_group_id, security_groups))[0]


def wait_for_rds_db_instance_to_become_available(rds_client):
    status = None

    print("Waiting for RDS DB instance to become available...")
    wait_periods = 30
    period_length = 30
    for _ in range(wait_periods):
        status = rds_client.describe_db_instances(
            DBInstanceIdentifier=DB_INSTANCE_NAME
        )["DBInstances"][0]["DBInstanceStatus"]
        if status == "available":
            print("RDS DB instance is available!")
            return
        if status == "failed":
            raise Exception(
                "An unexpected error occurred while waiting for the RDS DB instance to become available!"
            )

        sleep(period_length)

    print("RDS DB instance availability timeout")


def create_rds_secret(secrets_manager_client, rds_secret_name, rds_root_password):
    print("Creating RDS secret...")

    db_instance_info = get_db_instance_info()

    secret_string = json.dumps(
        {
            "username": f"{db_instance_info['MasterUsername']}",
            "password": f"{rds_root_password}",
            "database": f"{db_instance_info['DBName']}",
            "host": f"{db_instance_info['Endpoint']['Address']}",
            "port": f"{db_instance_info['Endpoint']['Port']}",
        }
    )

    secrets_manager_client.create_secret(
        Name=rds_secret_name,
        Description="Kubeflow RDS secret",
        SecretString=secret_string,
    )

    print("RDS secret created!")


def get_db_instance_info():
    rds_client = get_rds_client(CLUSTER_REGION)

    return rds_client.describe_db_instances(DBInstanceIdentifier=DB_INSTANCE_NAME)[
        "DBInstances"
    ][0]


def setup_cluster_secrets():
    print("=================================================================")
    print("                    Cluster Secrets Setup")
    print("=================================================================")

    setup_iam_service_account()
    setup_secrets_provider()


def setup_iam_service_account():
    create_secrets_iam_service_account()


def create_secrets_iam_service_account():
    print("Creating secrets IAM service account...")

    subprocess.run(
        [
            "eksctl",
            "create",
            "iamserviceaccount",
            "--name",
            "kubeflow-secrets-manager-sa",
            "--namespace",
            "kubeflow",
            "--cluster",
            CLUSTER_NAME,
            "--attach-policy-arn",
            "arn:aws:iam::aws:policy/AmazonSSMReadOnlyAccess",
            "--attach-policy-arn",
            "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
            "--approve",
            "--override-existing-serviceaccounts",
            "--region",
            CLUSTER_REGION,
        ]
    )

    print("Secrets IAM service account created!")


def setup_secrets_provider():
    print("Installing secrets provider...")
    install_secrets_store_csi_driver()
    print("Secrets provider install done!")


def install_secrets_store_csi_driver():
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretproviderclass.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/csidriver.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/secrets-store-csi-driver.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/v1.0.0/deploy/rbac-secretprovidersyncing.yaml"
    )
    kubectl_apply(
        "https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml"
    )


def setup_kubeflow():
    print("=================================================================")
    print("                        Kubeflow Setup")
    print("=================================================================")

    setup_kubeflow_pipeline()


def setup_kubeflow_pipeline():
    print("Setting up Kubeflow Pipeline...")

    print("Retrieving DB instance info...")
    try:
        db_instance_info = get_db_instance_info()
    except get_rds_client(CLUSTER_REGION).exceptions.DBInstanceNotFoundFault:
        print("Could not retrieve DB instance info, aborting Kubeflow pipeline setup!")
        return

    pipeline_params_env_file = "../../../awsconfigs/apps/pipeline/params.env"

    pipeline_params_env_lines = get_pipeline_params_env_lines(
        pipeline_params_env_file)

    new_pipeline_params_env_lines = get_updated_pipeline_params_env_lines(
        db_instance_info, pipeline_params_env_lines
    )

    edit_pipeline_params_env_file(
        new_pipeline_params_env_lines, pipeline_params_env_file
    )

    print("Kubeflow pipeline setup done!")


def get_pipeline_params_env_lines(pipeline_params_env_file):
    with open(pipeline_params_env_file, "r") as file:
        pipeline_params_env_lines = file.readlines()
    return pipeline_params_env_lines


def get_updated_pipeline_params_env_lines(db_instance_info, pipeline_params_env_lines):
    db_host_pattern = "dbHost="
    db_host_new_line = db_host_pattern + \
        db_instance_info["Endpoint"]["Address"] + "\n"

    db_mlmd_db_pattern = "mlmdDb="
    db_mlmd_db_new_line = db_mlmd_db_pattern + \
        db_instance_info["DBName"] + "\n"

    bucket_name_pattern = "bucketName="
    bucket_name_new_line = bucket_name_pattern + S3_BUCKET_NAME + "\n"

    minio_service_region_pattern = "minioServiceRegion="
    minio_service_region_new_line = minio_service_region_pattern + CLUSTER_REGION + "\n"

    new_pipeline_params_env_lines = []

    for line in pipeline_params_env_lines:
        line = replace_line(line, db_host_pattern, db_host_new_line)
        line = replace_line(line, db_mlmd_db_pattern, db_mlmd_db_new_line)
        line = replace_line(line, bucket_name_pattern, bucket_name_new_line)
        line = replace_line(
            line, minio_service_region_pattern, minio_service_region_new_line
        )
        new_pipeline_params_env_lines.append(line)

    return new_pipeline_params_env_lines


def replace_line(line, pattern, new_line):
    if line.startswith(pattern):
        return new_line
    else:
        return line


def edit_pipeline_params_env_file(
    new_pipeline_params_env_lines, pipeline_params_env_file
):
    print(f"Editing {pipeline_params_env_file} with appropriate values...")

    with open(pipeline_params_env_file, "w") as file:
        file.writelines(new_pipeline_params_env_lines)


def footer():
    print("=================================================================")
    print("                   RDS S3 Setup Complete")
    print("=================================================================")


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
parser.add_argument(
    "--bucket",
    type=str,
    metavar="S3_BUCKET",
    help="Your S3 bucket name (eg: mybucket)",
    required=True,
)
DB_ROOT_USER_DEFAULT = "admin"
parser.add_argument(
    "--db_root_user",
    type=str,
    default=DB_ROOT_USER_DEFAULT,
    help=f"Default is set to {DB_ROOT_USER_DEFAULT}",
    required=False,
)
parser.add_argument(
    "--db_root_password",
    type=str,
    help="AWS will generate a random password using secrets manager if no password is provided",
    required=False,
)
DB_INSTANCE_NAME_DEFAULT = "kubeflow-db"
parser.add_argument(
    "--db_instance_name",
    type=str,
    default=DB_INSTANCE_NAME_DEFAULT,
    help=f"Unique identifier for the RDS database instance. Default is set to {DB_INSTANCE_NAME_DEFAULT}",
    required=False,
)
DB_NAME_DEFAULT = "metadb"
parser.add_argument(
    "--db_name",
    type=str,
    default=DB_NAME_DEFAULT,
    help=f"Name of the metadata database. Default is set to {DB_NAME_DEFAULT}",
    required=False,
)
DB_INSTANCE_TYPE_DEFAULT = "db.m5.large"
parser.add_argument(
    "--db_instance_type",
    type=str,
    default=DB_INSTANCE_TYPE_DEFAULT,
    help=f"Default is set to {DB_INSTANCE_TYPE_DEFAULT}",
    required=False,
)
DB_INITIAL_STORAGE_DEFAULT = 50
parser.add_argument(
    "--db_initial_storage",
    type=int,
    default=DB_INITIAL_STORAGE_DEFAULT,
    help=f"Initial storage capacity in GB. Default is set to {DB_INITIAL_STORAGE_DEFAULT}",
    required=False,
)
DB_MAX_STORAGE_DEFAULT = 1000
parser.add_argument(
    "--db_max_storage",
    type=int,
    default=DB_MAX_STORAGE_DEFAULT,
    help=f"Maximum storage capacity in GB. Default is set to {DB_MAX_STORAGE_DEFAULT}",
    required=False,
)
DB_BACKUP_RETENTION_PERIOD_DEFAULT = 7
parser.add_argument(
    "--db_backup_retention_period",
    type=int,
    default=DB_BACKUP_RETENTION_PERIOD_DEFAULT,
    help=f"Default is set to {DB_BACKUP_RETENTION_PERIOD_DEFAULT}",
    required=False,
)
DB_STORAGE_TYPE_DEFAULT = "gp2"
parser.add_argument(
    "--db_storage_type",
    type=str,
    default=DB_STORAGE_TYPE_DEFAULT,
    help=f"Default is set to {DB_STORAGE_TYPE_DEFAULT}",
    required=False,
)
DB_SUBNET_GROUP_NAME_DEFAULT = "kubeflow-db-subnet-group"
parser.add_argument(
    "--db_subnet_group_name",
    type=str,
    default=DB_SUBNET_GROUP_NAME_DEFAULT,
    help=f"Default is set to {DB_SUBNET_GROUP_NAME_DEFAULT}",
    required=False,
)
parser.add_argument(
    "--s3_aws_access_key_id",
    type=str,
    help="""
    This parameter allows to explicitly specify the access key ID to use for the setup.
    The access key ID is used to create the S3 bucket and is saved using the secrets manager.
    """,
    required=True,
)
parser.add_argument(
    "--s3_aws_secret_access_key",
    type=str,
    help="""
    This parameter allows to explicitly specify the secret access key to use for the setup.
    The secret access key is used to create the S3 bucket and is saved using the secrets manager.
    """,
    required=True,
)
args, _ = parser.parse_known_args()

if __name__ == "__main__":
    CLUSTER_REGION = args.region
    CLUSTER_NAME = args.cluster
    S3_BUCKET_NAME = args.bucket
    S3_ACCESS_KEY_ID = args.s3_aws_access_key_id
    S3_SECRET_ACCESS_KEY = args.s3_aws_secret_access_key
    DB_ROOT_USER = args.db_root_user
    DB_ROOT_PASSWORD = args.db_root_password
    DB_INSTANCE_NAME = args.db_instance_name
    DB_NAME = args.db_name
    DB_INSTANCE_TYPE = args.db_instance_type
    DB_INITIAL_STORAGE = args.db_initial_storage
    DB_MAX_STORAGE = args.db_max_storage
    DB_BACKUP_RETENTION_PERIOD = args.db_backup_retention_period
    DB_STORAGE_TYPE = args.db_storage_type
    DB_SUBNET_GROUP_NAME = args.db_subnet_group_name

    main()
