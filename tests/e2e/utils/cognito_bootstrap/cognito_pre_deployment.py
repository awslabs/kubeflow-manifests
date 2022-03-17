# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

import logging

from e2e.fixtures import cluster
from e2e.utils.cognito_bootstrap import common as utils
from e2e.utils.config import configure_env_file

from e2e.utils.cognito_bootstrap.aws.acm import AcmCertificate
from e2e.utils.cognito_bootstrap.aws.cognito import CustomDomainCognitoUserPool
from e2e.utils.cognito_bootstrap.aws.iam import IAMPolicy
from e2e.utils.cognito_bootstrap.aws.route53 import Route53HostedZone
from e2e.utils.utils import (
    load_json_file,
    get_eks_client,
    get_ec2_client,
    rand_name,
)

from typing import Tuple


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Step 1: Create a subdomain for kubeflow deployment
def create_subdomain_hosted_zone(
    subdomain_name: str,
    root_domain_name: str,
    deployment_region: str,
    root_domain_hosted_zone_id: str = None,
) -> Tuple[Route53HostedZone, Route53HostedZone]:
    subdomain_hosted_zone = Route53HostedZone(
        domain=subdomain_name, region=deployment_region
    )

    subdomain_hosted_zone.create_zone()

    subdomain_hosted_zone.change_record_set(
        [
            subdomain_hosted_zone.generate_change_record(
                record_name=subdomain_name, record_type="A", record_value=["127.0.0.1"]
            )
        ]
    )

    subdomain_name_servers = subdomain_hosted_zone.get_name_servers()
    subdomains_NS_record = subdomain_hosted_zone.generate_change_record(
        record_name=subdomain_name,
        record_type="NS",
        record_value=subdomain_name_servers,
    )
    root_hosted_zone = None
    if root_domain_hosted_zone_id:
        root_hosted_zone = Route53HostedZone(
            domain=root_domain_name,
            id=root_domain_hosted_zone_id,
            region=deployment_region,
        )
        root_hosted_zone.change_record_set([subdomains_NS_record])
    else:
        logger.info(
            f"Since your {root_domain_name} hosted zone is not managed by route53, you will need to manually create a NS type record in {root_domain_name} for {subdomain_name} with value {subdomain_name_servers}"
        )
        input("Press any key once this step is complete")

    return root_hosted_zone, subdomain_hosted_zone


# Step 2: Create certificates
def create_certificates(
    deployment_region: str,
    subdomain_hosted_zone: Route53HostedZone,
    root_hosted_zone: Route53HostedZone = None,
) -> Tuple[AcmCertificate, AcmCertificate, AcmCertificate]:
    root_certificate = None
    if root_hosted_zone:
        root_certificate = AcmCertificate(
            domain="*." + root_hosted_zone.domain,
            hosted_zone=root_hosted_zone,
            region="us-east-1",
        )
        root_certificate.request_validation()
        validation_record = root_certificate.generate_domain_validation_record()
        root_certificate.create_domain_validation_records(validation_record)
        root_certificate.wait_for_certificate_validation()
    else:
        logger.info(
            f"Since your {root_hosted_zone.domain} hosted zone is not managed by route53, please create a certificate for *.{root_hosted_zone.domain} by following this document: https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html#request-public-console."
            "Make sure you validate your ceritificate using one of the methods mentioned in this document: https://docs.aws.amazon.com/acm/latest/userguide/domain-ownership-validation.html"
        )
        input("Press any key once the certificate status is ISSUED")

    subdomain_cert_n_virginia = AcmCertificate(
        domain="*." + subdomain_hosted_zone.domain,
        hosted_zone=subdomain_hosted_zone,
        region="us-east-1",
    )
    subdomain_cert_n_virginia.request_validation()

    subdomain_cert_deployment_region = subdomain_cert_n_virginia
    if deployment_region != "us-east-1":
        subdomain_cert_deployment_region = AcmCertificate(
            domain="*." + subdomain_hosted_zone.domain,
            hosted_zone=subdomain_hosted_zone,
            region=deployment_region,
        )
        subdomain_cert_deployment_region.request_validation()

    validation_record = subdomain_cert_n_virginia.generate_domain_validation_record()
    subdomain_cert_n_virginia.create_domain_validation_records(validation_record)
    subdomain_cert_n_virginia.wait_for_certificate_validation()
    subdomain_cert_deployment_region.wait_for_certificate_validation()

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
    userpool_cloudfront_alias = cognito_userpool.create_userpool_domain()
    subdomain_hosted_zone.change_record_set(
        [
            subdomain_hosted_zone.generate_change_record_type_alias_target(
                record_name=userpool_domain,
                record_type="A",
                hosted_zone_id=utils.CLOUDFRONT_HOSTED_ZONE_ID,
                dns_name=userpool_cloudfront_alias,
            )
        ]
    )
    cognito_userpool.wait_for_domain_status("ACTIVE")

    return cognito_userpool, userpool_cloudfront_alias


# Step 3: Configure Ingress and load balancer controller manifests
def configure_ingress(cognito_userpool: CustomDomainCognitoUserPool, tls_cert_arn: str):

    # annotate the ingress with auth related variables
    configure_env_file(
        env_file_path="../../awsconfigs/common/istio-ingress/overlays/cognito/params.env",
        env_dict={
            "CognitoUserPoolArn": cognito_userpool.arn,
            "CognitoAppClientId": cognito_userpool.client_id,
            "CognitoUserPoolDomain": cognito_userpool.userpool_domain,
            "certArn": tls_cert_arn,
        },
    )


def configure_alb_ingress_controller(
    region: str, cluster_name: str, policy_name: str = None
) -> Tuple[str, str]:
    policy_name = policy_name or rand_name(f"alb_ingress_controller_{cluster_name}")
    ec2_client = get_ec2_client(region)
    eks_client = get_eks_client(region)

    # create an iam service account with required permissions for the controller
    cluster.associate_iam_oidc_provider(cluster_name, region)
    alb_policy = IAMPolicy(
        name = policy_name,
        region=region
    )
    alb_policy.create(
        policy_document=load_json_file("../../awsconfigs/infra_configs/iam_alb_ingress_policy.json")
    )

    alb_sa_name = "alb-ingress-controller"
    cluster.create_iam_service_account(
        alb_sa_name, "kubeflow", cluster_name, region, [alb_policy.arn]
    )

    # tag cluster subnet with kubernetes.io/cluster/<cluster_name> tag
    # see prerequisites in https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html
    cluster_desc = eks_client.describe_cluster(name=cluster_name)
    ec2_client.create_tags(
        Resources=cluster_desc["cluster"]["resourcesVpcConfig"]["subnetIds"],
        Tags=[
            {"Key": f"kubernetes.io/cluster/{cluster_name}", "Value": "shared"},
        ],
    )

    # substitute the cluster_name for the load balancer controller
    configure_env_file(
        env_file_path="../../awsconfigs/common/aws-alb-ingress-controller/base/params.env",
        env_dict={
            "clusterName": cluster_name,
        },
    )

    return {
            "serviceAccount": {
                "name": alb_sa_name,
                "policyArn": alb_policy.arn
            }
        }


if __name__ == "__main__":
    utils.print_banner("Reading Config")
    cfg = utils.load_cfg()

    deployment_region = cfg["cluster"]["region"]
    cluster_name = cfg["cluster"]["name"]
    subdomain_name = cfg["route53"]["subDomain"]["name"]
    root_domain_name = cfg["route53"]["rootDomain"]["name"]
    root_domain_hosted_zone_id = cfg["route53"]["rootDomain"].get("hostedZoneId", None)

    utils.print_banner("Creating Subdomain in Route 53")
    root_hosted_zone, subdomain_hosted_zone = create_subdomain_hosted_zone(
        subdomain_name,
        root_domain_name,
        deployment_region,
        root_domain_hosted_zone_id,
    )
    cfg["route53"]["subDomain"]["hostedZoneId"] = subdomain_hosted_zone.id
    utils.write_cfg(cfg)

    utils.print_banner("Creating Certificate in ACM")
    (
        root_certificate,
        subdomain_cert_n_virginia,
        subdomain_cert_deployment_region,
    ) = create_certificates(deployment_region, subdomain_hosted_zone, root_hosted_zone)

    if root_certificate:
        cfg["route53"]["rootDomain"]["certARN"] = root_certificate.arn
    cfg["route53"]["subDomain"]["us-east-1-certARN"] = subdomain_cert_n_virginia.arn
    cfg["route53"]["subDomain"][
        deployment_region + "-certARN"
    ] = subdomain_cert_deployment_region.arn
    utils.write_cfg(cfg)

    utils.print_banner("Creating Cognito Userpool")
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
    utils.write_cfg(cfg)

    utils.print_banner("Configuring Ingress and load balancer controller manifests")
    configure_ingress(cognito_userpool, subdomain_cert_deployment_region.arn)
    alb_sa_details = configure_alb_ingress_controller(
        deployment_region, cluster_name
    )
    cfg["kubeflow"] = {
        "alb": alb_sa_details
    }
    utils.write_cfg(cfg)
