import subprocess
import boto3
import json
from e2e.utils.utils import get_aws_account_id

IAM_CLIENT = boto3.client(service_name='iam')

# Will create role and create/attach a policy if not already done.
def setup_role_and_policy(role_name, policy_name, trust_policy_file_name, permission_policy_file_name, create_trust_policy_file):    
    role_arn = create_iam_role_if_not_exist(role_name, trust_policy_file_name, create_trust_policy_file)
    print("role_arn:", role_arn)

    policy_arn = create_policy_if_not_exist(policy_name, permission_policy_file_name)
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
def create_policy_if_not_exist(policy_name, permission_policy_file_name):
    policy_arn = f'arn:aws:iam::{get_aws_account_id()}:policy/{policy_name}'
    try:
        IAM_CLIENT.get_policy(PolicyArn=policy_arn).get('Policy').get('Arn')
    except:
        print("Creating a new policy named", policy_name, "since there was no existing policy by this name.")
        
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

# Returns True if detachment is sucessfull, False otherwise.
def detach_IAM_policy(role_name, policy_name):
    policy_arn = f'arn:aws:iam::{get_aws_account_id()}:policy/{policy_name}'
    try:
        IAM_CLIENT.get_policy(PolicyArn=policy_arn).get('Policy').get('Arn')
    except:
        print("The policy named", policy_name, "does not exist, so deletion is not possible.")
        return False
    print("About to detach policy.")
    try:
        IAM_CLIENT.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    except Exception as e:
        print(e)
        return False
    return True
        
# Will detach the policy from the role and then delete the policy.
def delete_IAM_policy(policy_name):
    policy_arn = f'arn:aws:iam::{get_aws_account_id()}:policy/{policy_name}'
    print("About to delete policy with arn {policy_arn}")
    try:
        IAM_CLIENT.delete_policy(PolicyArn=policy_arn)
    except Exception as e:
        print("Triggered exception on deletion of policy.")
        print(e)
    print("After delete of policy attempt.")
    try:
        IAM_CLIENT.get_policy(PolicyArn=policy_arn).get('Policy').get('Arn')
    except:
        print("The policy named", policy_name, "was sucessfully deleted.")
        return
    raise AssertionError("The policy", policy_name, "was not successfully deleted.")

# Will delete the given IAM role.
def delete_IAM_role(role_name):
    print("Getting pre-delete role_arn.")
    try:
        role_arn = IAM_CLIENT.get_role(RoleName=role_name).get('Role').get('Arn')
    except:
        print("The role named", role_name, "does not exist, so deletion is not possible.")
        return
    print("About to delete role.")
    try:
        IAM_CLIENT.delete_role(RoleName=role_name)
    except Exception as e:
        print(e)
        return
    print("Role deleted.")
    print("Getting post-delete role_arn.")
    try:
        role_arn = IAM_CLIENT.get_role(RoleName=role_name).get('Role').get('Arn')
    except:
        print("The role named", role_name, "was sucessfully deleted.")
        return
    print("Role was not deleted properly")
    raise AssertionError(f"The role {role_name} was not successfully deleted.")
