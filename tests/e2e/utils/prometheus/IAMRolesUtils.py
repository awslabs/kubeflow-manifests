import subprocess
import boto3
import json

STS_CLIENT = boto3.client(service_name='sts')
IAM_CLIENT = boto3.client(service_name='iam')

# Get the AWS account ID
def get_AWS_account_ID():
    STS_CLIENT = boto3.client('sts')
    aws_account_id = STS_CLIENT.get_caller_identity().get('Account')
    return aws_account_id

# Will create role and create/attach a policy if not already done.
def setup_role_and_policy(role_name, policy_name, trust_policy_file_name, permission_policy_file_name, create_trust_policy_file, create_permission_policy_file):    
    role_arn = create_iam_role_if_not_exist(role_name, trust_policy_file_name, create_trust_policy_file)
    print("role_arn:", role_arn)

    policy_arn = create_policy_if_not_exist(policy_name, permission_policy_file_name, create_permission_policy_file)
    print("policy_arn:", policy_arn)

    attach_policy_to_role_if_not_attached(role_name, policy_name, policy_arn)

# Will create an iam role if there is no existing role with the given role name.    
def create_iam_role_if_not_exist(role_name, trust_policy_file_name, create_trust_policy_file):
    try:
        role_arn = IAM_CLIENT.get_role(RoleName=role_name).get('Role').get('Arn')
    except:
        print("Creating a new role named", role_name, "since there was no existing role by this name.")
        
        # Create a new role with a trust policy.
        create_trust_policy_file()
        with open(f'{trust_policy_file_name}.json') as trust_policy_file:
            trust_policy = json.dumps(json.load(trust_policy_file))
        role_arn = IAM_CLIENT.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=trust_policy
        ).get('Role').get('Arn')
    return role_arn

# Will create a permission policy if there is no existing policy with the given policy name.    
def create_policy_if_not_exist(policy_name, permission_policy_file_name, create_permission_policy_file):
    policy_arn = f'arn:aws:iam::{get_AWS_account_ID()}:policy/{policy_name}'
    try:
        IAM_CLIENT.get_policy(PolicyArn=policy_arn).get('Policy').get('Arn')
    except:
        print("Creating a new policy named", policy_name, "since there was no existing policy by this name.")
        
        # Create a permission policy for the new role.
        create_permission_policy_file()
        with open(f'{permission_policy_file_name}.json') as permission_policy_file:
            permission_policy = json.dumps(json.load(permission_policy_file))
        policy_arn = IAM_CLIENT.create_policy(
            PolicyName=policy_name,
            PolicyDocument=permission_policy
        ).get('Policy').get('Arn')
    return policy_arn

# Will attach the given policy to the given role if not already done.
def attach_policy_to_role_if_not_attached(role_name, policy_name, policy_arn):
    list_of_role_policies = IAM_CLIENT.list_attached_role_policies(RoleName=role_name).get('AttachedPolicies')
    need_to_add_policy = True
    for attached_policy in list_of_role_policies:
        if policy_name == attached_policy.get('PolicyName'):
            need_to_add_policy = False
            break
    if need_to_add_policy:
        print("Adding a policy named", policy_name, "to the role named", role_name, ".")
        # Attatch permission policy to role.
        IAM_CLIENT.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
    else:
        print("Policy named", policy_name, "is already attached to the role named", role_name, ".")
    
# Get the OIDC provider
def get_OIDC_provider(cluster_name, cluster_region):
    EKS_CLIENT = boto3.client(service_name='eks', region_name=cluster_region)
    https_oidc_provider = EKS_CLIENT.describe_cluster(
        name=cluster_name,
    ).get('cluster').get('identity').get('oidc').get('issuer')
    oidc_provider = https_oidc_provider.replace("https://", "", 1)
    print("oidc_provider:", oidc_provider)
    return oidc_provider
    
# Associate the OIDC Provider with the AWS IAM so it can accept and validate OIDC tokens.
def associate_OIDC_with_IAM(cluster_name, cluster_region):
    associate_iam_with_oidc_provider_command = f'eksctl utils associate-iam-oidc-provider --cluster {cluster_name} --region {cluster_region} --approve'.split()
    output_associate_iam_with_oidc_provider = subprocess.check_output(associate_iam_with_oidc_provider_command, encoding="utf-8")
    print("output_associate_iam_with_oidc_provider:", output_associate_iam_with_oidc_provider)
