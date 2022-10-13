# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

from e2e.utils.cognito_bootstrap import common
from e2e.utils.config import configure_env_file

from e2e.utils.aws.acm import AcmCertificate
from e2e.utils.aws.cognito import CustomDomainCognitoUserPool
from e2e.utils.aws.route53 import Route53HostedZone
from e2e.utils.load_balancer.setup_load_balancer import (
    create_subdomain_hosted_zone,
    create_certificates,
    configure_load_balancer_controller,
)
from e2e.utils.utils import print_banner, load_yaml_file, write_yaml_file, write_env_to_yaml

from typing import Tuple

INSTALLATION_PATH_FILE_COGNITO = "./resources/installation_config/cognito.yaml"
path_dic = load_yaml_file(INSTALLATION_PATH_FILE_COGNITO)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Step 2: Create certificates required for user pool and ALB
def create_certificates_cognito(
    deployment_region: str,
    subdomain_hosted_zone: Route53HostedZone,
    root_hosted_zone: Route53HostedZone = None,
) -> Tuple[AcmCertificate, AcmCertificate, AcmCertificate]:

    root_certificate, subdomain_cert_deployment_region = create_certificates(
        deployment_region, subdomain_hosted_zone, root_hosted_zone
    )

    subdomain_cert_n_virginia = subdomain_cert_deployment_region
    if deployment_region != "us-east-1":
        subdomain_cert_n_virginia = AcmCertificate(
            domain="*." + subdomain_hosted_zone.domain,
            hosted_zone=subdomain_hosted_zone,
            region="us-east-1",
        )
        subdomain_cert_n_virginia.request_validation()
        validation_record = (
            subdomain_cert_n_virginia.generate_domain_validation_record()
        )
        subdomain_cert_n_virginia.create_domain_validation_records(validation_record)
        subdomain_cert_n_virginia.wait_for_certificate_validation()

    return root_certificate, subdomain_cert_n_virginia, subdomain_cert_deployment_region


# Step 3: Create Cognito Userpool
def create_cognito_userpool(
    userpool_name,
    deployment_region: str,
    subdomain_hosted_zone: Route53HostedZone,
    userpool_domain_cert_arn: str,
) -> Tuple[CustomDomainCognitoUserPool, str]:
    subdomain_name = subdomain_hosted_zone.domain
    userpool_domain = "auth." + subdomain_name
    cognito_userpool = CustomDomainCognitoUserPool(
        userpool_name=userpool_name,
        userpool_domain=userpool_domain,
        domain_cert_arn=userpool_domain_cert_arn,
        region=deployment_region,
    )
    cognito_userpool.create_userpool()
    cognito_userpool.create_userpool_client(
        client_name="kubeflow",
        callback_urls=[f"https://kubeflow.{subdomain_name}/oauth2/idpresponse"],
        logout_urls=[f"https://kubeflow.{subdomain_name}"],
    )
    subdomain_hosted_zone.change_record_set(
        [
            subdomain_hosted_zone.generate_change_record(
                record_name=subdomain_name, record_type="A", record_value=["127.0.0.1"]
            )
        ]
    )
    userpool_cloudfront_alias = cognito_userpool.create_userpool_domain()
    subdomain_hosted_zone.change_record_set(
        [
            subdomain_hosted_zone.generate_change_record_type_alias_target(
                record_name=userpool_domain,
                record_type="A",
                hosted_zone_id=common.CLOUDFRONT_HOSTED_ZONE_ID,
                dns_name=userpool_cloudfront_alias,
            )
        ]
    )
    cognito_userpool.wait_for_domain_status("ACTIVE")

    return cognito_userpool, userpool_cloudfront_alias


# Step 3: Configure Ingress
#TO DO: The current script fills in Helm values and Kustomize params.env files at the same time. Need to decouple the two in future.  
def configure_ingress(cognito_userpool: CustomDomainCognitoUserPool, tls_cert_arn: str, load_balancer_scheme="internet-facing"):
    ingress_helm_path = path_dic["ingress"]["installation_options"]["helm"]["paths"]
    ingress_values_file = f"{ingress_helm_path}/values.yaml"
    cognito_dict = {
            "CognitoUserPoolArn": cognito_userpool.arn,
            "CognitoAppClientId": cognito_userpool.client_id,
            "CognitoUserPoolDomain": cognito_userpool.userpool_domain,
            "certArn": tls_cert_arn,
    }

    # annotate the ingress with ALB listener rule parameters
    configure_env_file(
        env_file_path="../../awsconfigs/common/istio-ingress/overlays/cognito/params.env",
        env_dict = cognito_dict
    )

    #annotate loadBalancerScheme
    configure_env_file(
        env_file_path="../../awsconfigs/common/istio-ingress/base/params.env",
        env_dict={
            "loadBalancerScheme": load_balancer_scheme
        },
    )

    cognito_helm_dict = {
        "cognito": {
            "appClientId": cognito_userpool.client_id,
            "UserPoolArn": cognito_userpool.arn,
            "UserPoolDomain": cognito_userpool.userpool_domain,
        },
        "certArn": tls_cert_arn,
        "scheme": load_balancer_scheme
    }

    write_env_to_yaml(cognito_helm_dict, ingress_values_file, "alb")

#TO DO: The current script fills in Helm values and Kustomize params.env files at the same time. Need to decouple the two in future.
def configure_aws_authservice(
    cognito_userpool: CustomDomainCognitoUserPool, subdomain_name: str
):
    aws_auth_service_helm_path = path_dic["aws-authservice"]["installation_options"]["helm"]["paths"]
    aws_auth_service_values_file = f"{aws_auth_service_helm_path}/values.yaml"
    logout_url_dict = {
        "LOGOUT_URL": f"https://{cognito_userpool.userpool_domain}/logout?client_id={cognito_userpool.client_id}&logout_uri=https://kubeflow.{subdomain_name}"
    }
    # substitute the LOGOUT_URL for the AWS AuthService to redirect to
    configure_env_file(
        env_file_path="../../awsconfigs/common/aws-authservice/base/params.env",
        env_dict = logout_url_dict
    )

    write_env_to_yaml(logout_url_dict, aws_auth_service_values_file)
    
if __name__ == "__main__":
    config_file_path = common.CONFIG_FILE
    print_banner("Reading Config")
    cfg = load_yaml_file(file_path=config_file_path)

    deployment_region = cfg["cluster"]["region"]
    cluster_name = cfg["cluster"]["name"]
    subdomain_name = cfg["route53"]["subDomain"]["name"]
    root_domain_name = cfg["route53"]["rootDomain"]["name"]
    root_domain_hosted_zone_id = cfg["route53"]["rootDomain"].get("hostedZoneId", None)
    load_balancer_scheme = cfg["kubeflow"]["alb"]["scheme"]

    print_banner("Creating Subdomain in Route 53")
    root_hosted_zone, subdomain_hosted_zone = create_subdomain_hosted_zone(
        subdomain_name,
        root_domain_name,
        deployment_region,
        root_domain_hosted_zone_id,
    )
    cfg["route53"]["subDomain"]["hostedZoneId"] = subdomain_hosted_zone.id
    write_yaml_file(yaml_content=cfg, file_path=config_file_path)

    print_banner("Creating Certificate in ACM")
    (
        root_certificate,
        subdomain_cert_n_virginia,
        subdomain_cert_deployment_region,
    ) = create_certificates_cognito(
        deployment_region, subdomain_hosted_zone, root_hosted_zone
    )

    if root_certificate:
        cfg["route53"]["rootDomain"]["certARN"] = root_certificate.arn
    cfg["route53"]["subDomain"]["us-east-1-certARN"] = subdomain_cert_n_virginia.arn
    cfg["route53"]["subDomain"][
        deployment_region + "-certARN"
    ] = subdomain_cert_deployment_region.arn
    write_yaml_file(yaml_content=cfg, file_path=config_file_path)

    print_banner("Creating Cognito Userpool")
    userpool_name = cfg["cognitoUserpool"]["name"]
    cognito_userpool, userpool_cloudfront_alias = create_cognito_userpool(
        userpool_name,
        deployment_region,
        subdomain_hosted_zone,
        subdomain_cert_n_virginia.arn,
    )
    cfg["cognitoUserpool"]["ARN"] = cognito_userpool.arn
    cfg["cognitoUserpool"]["appClientId"] = cognito_userpool.client_id
    cfg["cognitoUserpool"]["domain"] = cognito_userpool.userpool_domain
    cfg["cognitoUserpool"]["domainAliasTarget"] = cognito_userpool.cloudfront_domain
    write_yaml_file(yaml_content=cfg, file_path=config_file_path)

    print_banner("Configuring Ingress and load balancer controller manifests")
    configure_ingress(cognito_userpool, subdomain_cert_deployment_region.arn, load_balancer_scheme)
    configure_aws_authservice(cognito_userpool, subdomain_hosted_zone.domain)
    alb_sa_details = configure_load_balancer_controller(deployment_region, cluster_name)
    cfg["kubeflow"] = {"alb": alb_sa_details}
    cfg["kubeflow"]["alb"]["scheme"] = load_balancer_scheme
    write_yaml_file(yaml_content=cfg, file_path=config_file_path)
