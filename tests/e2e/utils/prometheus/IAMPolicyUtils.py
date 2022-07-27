import boto3
import json
from e2e.utils.utils import get_aws_account_id

IAM_CLIENT = boto3.client(service_name='iam')

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

# Will try to delete the given IAM policy.
def delete_IAM_policy(policy_name):
    policy_arn = f'arn:aws:iam::{get_aws_account_id()}:policy/{policy_name}'
    print("Attempting to delete policy with arn {policy_arn}")
    try:
        IAM_CLIENT.delete_policy(PolicyArn=policy_arn)
    except Exception as e:
        print("Triggered exception on deletion of policy.")
        print(e)
    try:
        IAM_CLIENT.get_policy(PolicyArn=policy_arn).get('Policy').get('Arn')
    except:
        print("The policy named", policy_name, "was sucessfully deleted.")
        return
    raise AssertionError("The policy", policy_name, "was not successfully deleted.")
