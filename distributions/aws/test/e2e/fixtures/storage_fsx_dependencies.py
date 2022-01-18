import time
import pytest
import subprocess
import boto3

from e2e.utils.config import metadata
from e2e.utils.cognito_bootstrap.common import load_cfg, write_cfg
from e2e.fixtures.kustomize import kustomize, configure_manifests
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
    get_fsx_client,
    kubectl_apply,
    kubectl_delete,
    kubectl_apply_kustomize,
    kubectl_delete_kustomize,
)

DEFAULT_NAMESPACE = "kube-system"


def wait_on_fsx_status(desired_status, fsx_client, file_system_id):
    def callback():
        response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
        filesystem_status = response["FileSystems"][0]["Lifecycle"]
        print(f"{file_system_id} {filesystem_status} .... waiting")
        assert filesystem_status == desired_status

    wait_for(callback, 600)


def get_fsx_dns_name(fsx_client, file_system_id):
    response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
    return response["FileSystems"][0]["DNSName"]


def get_fsx_mount_name(fsx_client, file_system_id):
    response = fsx_client.describe_file_systems(FileSystemIds=[file_system_id])
    return response["FileSystems"][0]["LustreConfiguration"]["MountName"]


@pytest.fixture(scope="class")
def install_fsx_csi_driver(metadata, region, request, cluster, kustomize):
    fsx_driver = {}
    FSx_DRIVER_VERSION = "v0.7.1"
    FSx_CSI_DRIVER = f"github.com/kubernetes-sigs/aws-fsx-csi-driver/deploy/kubernetes/overlays/stable/?ref=tags/{FSx_DRIVER_VERSION}"

    def on_create():
        kubectl_apply_kustomize(FSx_CSI_DRIVER)
        fsx_driver["driver_version"] = FSx_DRIVER_VERSION

    def on_delete():
        kubectl_delete_kustomize(FSx_CSI_DRIVER)

    return configure_resource_fixture(
        metadata, request, fsx_driver, "fsx_driver", on_create, on_delete
    )


@pytest.fixture(scope="class")
def create_fsx_driver_sa(
    metadata, region, request, cluster, account_id, install_fsx_csi_driver
):
    # TODO: Existing IAM Client with Region does not seem to work.
    fsx_deps = {}
    iam_client = boto3.client("iam")

    FSx_POLICY_DOCUMENT = (
        "../../examples/storage/fsx-for-lustre/fsx-csi-driver-policy.json"
    )
    policy_name = rand_name("fsx-iam-policy-")
    policy_arn = [f"arn:aws:iam::{account_id}:policy/{policy_name}"]

    def on_create():
        associate_iam_oidc_provider(cluster, region)

        with open(FSx_POLICY_DOCUMENT, "r") as myfile:
            policy = myfile.read()

        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=policy,
        )
        assert response["Policy"]["Arn"] is not None

        create_iam_service_account(
            "fsx-csi-controller-sa", DEFAULT_NAMESPACE, cluster, region, policy_arn
        )
        fsx_deps["fsx_iam_policy_name"] = policy_name

    def on_delete():
        details_fsx_deps = metadata.get("fsx_deps") or fsx_deps
        policy_name = details_fsx_deps["fsx_iam_policy_name"]
        iam_client.delete_policy(
            PolicyName=policy_name,
        )

    return configure_resource_fixture(
        metadata, request, fsx_deps, "fsx_deps", on_create, on_delete
    )


@pytest.fixture(scope="class")
def create_fsx_volume(metadata, region, request, cluster, create_fsx_driver_sa):
    fsx_volume = {}
    eks_client = get_eks_client(region)
    ec2_client = get_ec2_client(region)
    fsx_client = get_fsx_client(region)

    def on_create():
        # Get VPC ID, Cluster security group
        response = eks_client.describe_cluster(name=cluster)
        vpc_id = response["cluster"]["resourcesVpcConfig"]["vpcId"]
        cluster_security_group = response["cluster"]["resourcesVpcConfig"][
            "clusterSecurityGroupId"
        ]
        subnet_id = response["cluster"]["resourcesVpcConfig"]["subnetIds"][0]

        # Create Security Group
        security_group_name = rand_name("fsx-security-group-")
        response = ec2_client.create_security_group(
            VpcId=vpc_id,
            GroupName=security_group_name,
            Description="My fsx security group",
        )
        fsx_volume["security_group_id"] = security_group_id = response["GroupId"]

        # Open Port for CIDR Range
        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": 988,
                    "ToPort": 988,
                    "IpProtocol": "tcp",
                    "UserIdGroupPairs": [{"GroupId": security_group_id}],
                },
            ],
        )

        ec2_client.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    "FromPort": 988,
                    "ToPort": 988,
                    "IpProtocol": "tcp",
                    "UserIdGroupPairs": [{"GroupId": cluster_security_group}],
                },
            ],
        )

        # Create an Amazon fsx FileSystem for your EKS Cluster
        response = fsx_client.create_file_system(
            FileSystemType="LUSTRE",
            SubnetIds=[subnet_id],
            SecurityGroupIds=[security_group_id],
            StorageCapacity=1200,
        )
        file_system_id = response["FileSystem"]["FileSystemId"]

        # Check for status of filesystem to be "available" before creating mount targets
        wait_on_fsx_status("AVAILABLE", fsx_client, file_system_id)

        # Write the FileSystemDetails to the metadata file
        fsx_volume["file_system_id"] = file_system_id
        fsx_volume["dns_name"] = get_fsx_dns_name(fsx_client, file_system_id)
        fsx_volume["mount_name"] = get_fsx_mount_name(fsx_client, file_system_id)

    def on_delete():
        # Get FileSystem_ID
        details_fsx_volume = metadata.get("fsx_volume") or fsx_volume
        fs_id = details_fsx_volume["file_system_id"]
        sg_id = details_fsx_volume["security_group_id"]

        # Delete the Filesystem, does not provide a deleted status hence can't check delete status
        fsx_client.delete_file_system(
            FileSystemId=fs_id,
        )

        # Delete the Security Group
        ec2_client.delete_security_group(GroupId=sg_id)

    return configure_resource_fixture(
        metadata, request, fsx_volume, "fsx_volume", on_create, on_delete
    )


@pytest.fixture(scope="class")
def static_provisioning(metadata, region, request, cluster, create_fsx_volume):
    details_fsx_volume = metadata.get("fsx_volume")
    fs_id = details_fsx_volume["file_system_id"]
    dns_name = details_fsx_volume["dns_name"]
    mount_name = details_fsx_volume["mount_name"]
    claim_name = rand_name("fsx-claim-")
    fsx_pv_filepath = (
        "../../examples/storage/fsx-for-lustre/static-provisioning/pv.yaml"
    )
    fsx_pvc_filepath = (
        "../../examples/storage/fsx-for-lustre/static-provisioning/pvc.yaml"
    )
    fsx_claim = {}

    def on_create():
        # Add the filesystem_id to the pv.yaml file
        fsx_pv = load_cfg(fsx_pv_filepath)
        fsx_pv["spec"]["csi"]["volumeHandle"] = fs_id
        fsx_pv["metadata"]["name"] = claim_name
        fsx_pv["spec"]["csi"]["volumeAttributes"]["dnsname"] = dns_name
        fsx_pv["spec"]["csi"]["volumeAttributes"]["mountname"] = mount_name
        write_cfg(fsx_pv, fsx_pv_filepath)

        # Add the namespace to the pvc.yaml file
        fsx_pvc = load_cfg(fsx_pvc_filepath)
        fsx_pvc["metadata"]["namespace"] = DEFAULT_NAMESPACE
        fsx_pvc["metadata"]["name"] = claim_name
        write_cfg(fsx_pvc, fsx_pvc_filepath)

        kubectl_apply(fsx_pv_filepath)
        kubectl_apply(fsx_pvc_filepath)

        fsx_claim["claim_name"] = claim_name

    def on_delete():
        kubectl_delete(fsx_pvc_filepath)
        kubectl_delete(fsx_pv_filepath)

    return configure_resource_fixture(
        metadata, request, fsx_claim, "fsx_claim", on_create, on_delete
    )
