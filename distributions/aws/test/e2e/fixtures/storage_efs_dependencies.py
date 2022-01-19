import time
import pytest
import subprocess
import boto3

from e2e.utils.config import metadata
from e2e.fixtures.kustomize import kustomize, configure_manifests
from e2e.utils.cognito_bootstrap.common import load_cfg, write_cfg
from e2e.conftest import region
from e2e.fixtures.cluster import cluster
from e2e.fixtures.clients import account_id
from e2e.utils.utils import rand_name
from e2e.utils.config import configure_resource_fixture
from e2e.fixtures.cluster import associate_iam_oidc_provider, create_iam_service_account
from e2e.utils.utils import (
    rand_name,
    wait_for,
    get_iam_client,
    get_eks_client,
    get_ec2_client,
    get_efs_client,
    curl_file_to_path,
    kubectl_apply,
    kubectl_delete,
    kubectl_apply_kustomize,
    kubectl_delete_kustomize,
)

DEFAULT_NAMESPACE = "kube-system"


def wait_on_efs_status(desired_status, efs_client, file_system_id):
    def callback():
        response = efs_client.describe_file_systems(
            FileSystemId=file_system_id,
        )
        filesystem_status = response["FileSystems"][0]["LifeCycleState"]
        print(f"{file_system_id} {filesystem_status} .... waiting")
        assert filesystem_status == desired_status

    wait_for(callback)


@pytest.fixture(scope="class")
def install_efs_csi_driver(metadata, region, request, cluster, kustomize):
    efs_driver = {}
    EFS_DRIVER_VERSION = "v1.3.4"
    EFS_CSI_DRIVER = f"github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=tags/{EFS_DRIVER_VERSION}"

    def on_create():
        kubectl_apply_kustomize(EFS_CSI_DRIVER)
        efs_driver["driver_version"] = EFS_DRIVER_VERSION

    def on_delete():
        kubectl_delete_kustomize(EFS_CSI_DRIVER)

    return configure_resource_fixture(
        metadata, request, efs_driver, "efs_driver", on_create, on_delete
    )


@pytest.fixture(scope="class")
def create_efs_driver_sa(
    metadata, region, request, cluster, account_id, install_efs_csi_driver
):
    # TODO: Existing IAM Client with Region does not seem to work.
    efs_deps = {}
    iam_client = boto3.client("iam")

    EFS_IAM_POLICY = "https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/v1.3.4/docs/iam-policy-example.json"
    policy_name = rand_name("efs-iam-policy-")
    policy_arn = [f"arn:aws:iam::{account_id}:policy/{policy_name}"]

    def on_create():
        associate_iam_oidc_provider(cluster, region)
        curl_file_to_path(EFS_IAM_POLICY, "iam-policy-example.json")
        with open("iam-policy-example.json", "r") as myfile:
            policy = myfile.read()

        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy,
        )
        assert response["Policy"]["Arn"] is not None

        create_iam_service_account(
            "efs-csi-controller-sa", DEFAULT_NAMESPACE, cluster, region, policy_arn
        )
        efs_deps["efs_iam_policy_name"] = policy_name

    def on_delete():
        details_efs_deps = metadata.get("efs_deps") or efs_deps
        policy_name = details_efs_deps["efs_iam_policy_name"]
        iam_client.delete_policy(
            PolicyName=policy_name,
        )

    return configure_resource_fixture(
        metadata, request, efs_deps, "efs_deps", on_create, on_delete
    )


@pytest.fixture(scope="class")
def create_efs_volume(metadata, region, request, cluster, create_efs_driver_sa):
    efs_volume = {}
    eks_client = get_eks_client(region)
    ec2_client = get_ec2_client(region)
    efs_client = get_efs_client(region)

    def on_create():
        # Get VPC ID
        response = eks_client.describe_cluster(name=cluster)
        vpc_id = response["cluster"]["resourcesVpcConfig"]["vpcId"]

        # Get CIDR Range
        response = ec2_client.describe_vpcs(
            VpcIds=[
                vpc_id,
            ]
        )
        cidr_ip = response["Vpcs"][0]["CidrBlock"]

        # Create Security Group
        security_group_name = rand_name("efs-security-group-")
        response = ec2_client.create_security_group(
            VpcId=vpc_id,
            GroupName=security_group_name,
            Description="My EFS security group",
        )
        security_group_id = response["GroupId"]
        efs_volume["security_group_id"] = security_group_id

        # Open Port for CIDR Range
        response = ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            FromPort=2049,
            ToPort=2049,
            CidrIp=cidr_ip,
            IpProtocol="tcp",
        )

        # Create an Amazon EFS FileSystem for your EKS Cluster
        response = efs_client.create_file_system(
            PerformanceMode="generalPurpose",
        )
        file_system_id = response["FileSystemId"]

        # Check for status of filesystem to be "available" before creating mount targets
        wait_on_efs_status("available", efs_client, file_system_id)

        # Get Subnet Ids
        response = ec2_client.describe_subnets(
            Filters=[
                {
                    "Name": "vpc-id",
                    "Values": [
                        vpc_id,
                    ],
                },
            ]
        )

        # Create Mount Targets for each subnet - TODO: Check how many subnets this needs to be added to.
        subnets = response["Subnets"]
        for subnet in subnets:
            subnet_id = subnet["SubnetId"]
            response = efs_client.create_mount_target(
                FileSystemId=file_system_id,
                SecurityGroups=[
                    security_group_id,
                ],
                SubnetId=subnet_id,
            )

        # Write the FileSystemId to the metadata file
        efs_volume["file_system_id"] = file_system_id

    def on_delete():
        # Get FileSystem_ID
        details_efs_volume = metadata.get("efs_volume") or efs_volume
        fs_id = details_efs_volume["file_system_id"]
        sg_id = details_efs_volume["security_group_id"]

        # Delete the Mount Targets
        response = efs_client.describe_mount_targets(
            FileSystemId=fs_id,
        )
        existing_mount_targets = response["MountTargets"]
        for mount_target in existing_mount_targets:
            mount_target_id = mount_target["MountTargetId"]
            efs_client.delete_mount_target(
                MountTargetId=mount_target_id,
            )

        # Delete the Filesystem
        efs_client.delete_file_system(
            FileSystemId=fs_id,
        )
        wait_on_efs_status("deleted", efs_client, fs_id)

        # Delete the Security Group
        ec2_client.delete_security_group(GroupId=sg_id)

    return configure_resource_fixture(
        metadata, request, efs_volume, "efs_volume", on_create, on_delete
    )


@pytest.fixture(scope="class")
def static_provisioning(metadata, region, request, cluster, create_efs_volume):
    details_efs_volume = metadata.get("efs_volume")
    fs_id = details_efs_volume["file_system_id"]
    claim_name = rand_name("efs-claim-")
    efs_sc_filepath = "../../examples/storage/efs/static-provisioning/sc.yaml"
    efs_pv_filepath = "../../examples/storage/efs/static-provisioning/pv.yaml"
    efs_pvc_filepath = "../../examples/storage/efs/static-provisioning/pvc.yaml"
    efs_claim = {}

    def on_create():
        # Add the filesystem_id to the pv.yaml file
        efs_pv = load_cfg(efs_pv_filepath)
        efs_pv["spec"]["csi"]["volumeHandle"] = fs_id
        efs_pv["metadata"]["name"] = claim_name
        write_cfg(efs_pv, efs_pv_filepath)

        # Add the namespace to the pvc.yaml file
        efs_pvc = load_cfg(efs_pvc_filepath)
        efs_pvc["metadata"]["namespace"] = DEFAULT_NAMESPACE
        efs_pvc["metadata"]["name"] = claim_name
        write_cfg(efs_pvc, efs_pvc_filepath)

        kubectl_apply(efs_sc_filepath)
        kubectl_apply(efs_pv_filepath)
        kubectl_apply(efs_pvc_filepath)

        efs_claim["claim_name"] = claim_name

    def on_delete():
        kubectl_delete(efs_pvc_filepath)
        kubectl_delete(efs_pv_filepath)
        kubectl_delete(efs_sc_filepath)

    return configure_resource_fixture(
        metadata, request, efs_claim, "efs_claim", on_create, on_delete
    )
