import boto3
import datetime

client = boto3.client("iam")


response = client.list_open_id_connect_providers()

oidc_provider_list = response["OpenIDConnectProviderList"]


filter_date = datetime.datetime(2022, 1, 1)
for oidc_provider in oidc_provider_list:
    oidc_arn = oidc_provider["Arn"]
    oidc = client.get_open_id_connect_provider(OpenIDConnectProviderArn=oidc_arn)
    create_date = oidc["CreateDate"]
    filter_date = filter_date.replace(tzinfo=oidc["CreateDate"].tzinfo)
    # print(create_date, filter_date, create_date < filter_date)
    if create_date < filter_date:
        client.delete_open_id_connect_provider(oidc_arn)
