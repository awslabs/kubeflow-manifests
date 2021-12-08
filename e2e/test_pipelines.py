from os import access
import os
import random
import string
import subprocess
import pytest
import boto3
import time
import tempfile

def create_cluster(cluster_name, cluster_region, cluster_version='1.19'):
    cmd = []
    cmd += "eksctl create cluster".split()
    cmd += f"--name {cluster_name}".split()
    cmd += f"--version {cluster_version}".split()
    cmd += f"--region {cluster_region}".split()
    cmd += "--node-type m5.xlarge".split()
    cmd += "--nodes 5".split()
    cmd += "--nodes-min 1".split()
    cmd += "--nodes-max 10".split()
    cmd += "--managed".split()

    retcode = subprocess.call(cmd)
    if retcode != 0:
        raise "Failed to create cluster"

def delete_cluster(cluster_name, cluster_region):
    cmd = []
    cmd += "eksctl create cluster".split()
    cmd += f"--name {cluster_name}".split()
    cmd += f"--region {cluster_region}".split()

    retcode = subprocess.call(cmd)
    if retcode != 0:
        raise "Failed to delete cluster"

@pytest.fixture
def cluster_region():
    return "ap-south-1"

@pytest.fixture
def cluster(cluster_region):
    # cluster_name = rand_name("e2e-test-cluster-")
    cluster_name = "kubeflow-e2e-testing"

    # create_cluster(cluster_name, cluster_region)
    yield cluster_name
    # delete_cluster(cluster_name, cluster_region)

@pytest.fixture
def s3_client(cluster_region):
    return boto3.client('s3', region_name=cluster_region)

@pytest.fixture
def bucket(s3_client, cluster_region):
    bucket_name = rand_name("e2e-test-bucket-")

    s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={
                'LocationConstraint': cluster_region
            },
    )

    yield bucket_name

    s3_client.delete_bucket(
            Bucket=bucket_name,
    )

@pytest.fixture
def ec2_client(cluster_region):
    return boto3.client('ec2', region_name=cluster_region)

@pytest.fixture
def rds_client(cluster_region):
    return boto3.client('rds', region_name=cluster_region)

@pytest.fixture
def rds_db_subnet_group(ec2_client, rds_client, cluster):
    def get_private_subnets():
        response = ec2_client.describe_subnets(
            Filters=[
                {
                    'Name': 'tag:alpha.eksctl.io/cluster-name',
                    'Values': [cluster],
                },
                {
                    'Name': 'tag:aws:cloudformation:logical-id',
                    'Values': ["SubnetPublic*"],
                },
            ],
        )
        assert len(response['Subnets']) >= 2
        return [s['SubnetId'] for s in response['Subnets']]

    private_subnets = wait_for(get_private_subnets)
    print(private_subnets)
    
    db_subnet_group_name = rand_name("e2e-test-db-subnet-group-")

    create_resp = rds_client.create_db_subnet_group(
        DBSubnetGroupName=db_subnet_group_name,
        DBSubnetGroupDescription="For e2e testing",
        SubnetIds=private_subnets
    )

    yield create_resp['DBSubnetGroup']

    rds_client.delete_db_subnet_group(
        DBSubnetGroupName=db_subnet_group_name,
    )

@pytest.fixture
def rds_instance(ec2_client, rds_client, cluster, rds_db_subnet_group):
    def get_vpc_id():
        response = ec2_client.describe_vpcs(
            Filters=[
                {
                    'Name': 'tag:alpha.eksctl.io/cluster-name',
                    'Values': [cluster],
                },
            ],
        )
        assert len(response['Vpcs']) == 1
        return response['Vpcs'][0]['VpcId']
    
    vpc_id = wait_for(get_vpc_id)
    print("vpc", vpc_id)

    def get_instance_security_group():
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:eks:cluster-name',
                    'Values': [cluster],
                }
            ],
        )
        instances = [i for r in response['Reservations'] for i in r['Instances']]
        assert len(instances) > 0
        security_groups = [i['SecurityGroups'][0]['GroupId'] for i in instances]
        assert len(security_groups) > 0

        return security_groups[0]

    instance_security_group = wait_for(get_instance_security_group)
    print(instance_security_group)

    db_id = rand_name("e2e-test-db-instance-")

    # todo: add publicly accessible
    rds_client.create_db_instance(
        DBName='kubeflow',
        DBInstanceIdentifier=db_id,
        AllocatedStorage= 20,
        DBInstanceClass='db.m5.large',
        Engine='MySQL',
        EngineVersion='8.0.17',
        MultiAZ=False,
        MasterUsername='admin',
        MasterUserPassword='Kubefl0w',
        DBSubnetGroupName=rds_db_subnet_group['DBSubnetGroupName'],
        PubliclyAccessible=True,
        VpcSecurityGroupIds=[instance_security_group]
    )

    def ensure_created():
        response = rds_client.describe_db_instances(
            DBInstanceIdentifier=db_id
        )
        assert response['DBInstances'][0]['DBInstanceStatus'] in {'available', 'backing-up'}
        return response['DBInstances'][0]
    
    db_instance = wait_for(ensure_created, timeout=300)

    yield db_instance

    rds_client.delete_db_instance(
        DBInstanceIdentifier=db_id,
        SkipFinalSnapshot=True,
        DeleteAutomatedBackups=True
    )

    def ensure_deleted():
        try:
            rds_client.describe_db_instances(
                DBInstanceIdentifier=db_id
            )
        except rds_client.exceptions.DBInstanceNotFoundFault:
            return
        except Exception as e:
            raise e
        
        raise AssertionError("DB instance expected to be deleted but still exists")
    
    wait_for(ensure_deleted, timeout=10*60)

def apply_kustomize(path):
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        apply_retcode = subprocess.call(f"kubectl apply -f {tmp.name}".split())
        assert apply_retcode == 0

def delete_kustomize(path):
    with tempfile.NamedTemporaryFile() as tmp:
        build_retcode = subprocess.call(f"kustomize build {path} -o {tmp.name}".split())
        assert build_retcode == 0
        subprocess.call(f"kubectl delete -f {tmp.name}".split())


PIPELINES_SECRET_ENV_PATH = "../apps/pipeline/upstream/env/aws/secret.env"
PIPELINES_PARAMS_ENV_PATH = "../apps/pipeline/upstream/env/aws/params.env"
PIPELINES_MINIO_PATCH_ENV_PATH = "../apps/pipeline/upstream/env/aws/minio-artifact-secret-patch.env"

@pytest.fixture
def minio_credentials():
    access_key = os.environ.get('MINIO_ACCESS_KEY')
    secret_key = os.environ.get('MINIO_SECRET_KEY')

    if not access_key or not secret_key:
        raise AssertionError("Minio access key and secret key must be present")

    return {
        'AccessKey': access_key,
        'SecretKey': secret_key
    }
    
GENERIC_KUSTOMIZE_MANIFEST_PATH = "./manifests/generic"
PIPELINE_S3_KUSTOMIZE_MANIFEST_PATH = "./manifests/pipelines/s3"

# def test_s3_folders_created(cluster, rds_instance, bucket, minio_credentials, cluster_region):
#     print(rds_instance)

#     with open(PIPELINES_SECRET_ENV_PATH, 'w') as file:
#         file.write("username=admin\n")
#         file.write("password=Kubefl0w\n")

#     with open(PIPELINES_PARAMS_ENV_PATH, 'w') as file:
#         file.write(f"dbHost={rds_instance['Endpoint']['Address']}\n")
#         file.write(f"bucketName={bucket}\n")
#         file.write("minioServiceHost=s3.amazonaws.com\n")
#         file.write(f"minioServiceRegion={cluster_region}\n")
    
#     with open(PIPELINES_MINIO_PATCH_ENV_PATH, 'w') as file:
#         file.write(f"accesskey={minio_credentials['AccessKey']}\n")
#         file.write(f"secretkey={minio_credentials['SecretKey']}\n")

#     print("starting apply")
#     wait_for(lambda : apply_kustomize(PIPELINE_S3_KUSTOMIZE_MANIFEST_PATH), timeout=20*60)

#     input("hit enter... ")

#     print("starting delete")
#     delete_kustomize(PIPELINE_S3_KUSTOMIZE_MANIFEST_PATH)

#     assert 1 == 0

# change timeout to 300
def wait_for(callback, timeout=0, interval=10):
    start = time.time()
    while True:
        try:
            return callback()
        except Exception as e:
            if time.time() - start >= timeout:
                raise e
            time.sleep(interval)

def rand_name(prefix):
    suffix = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return prefix + suffix

if __name__ == "__main__":
    pass
