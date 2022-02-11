import logging
from e2e.utils.cognito_bootstrap import common as utils

from e2e.utils.cognito_bootstrap.aws.acm import AcmCertificate
from e2e.utils.cognito_bootstrap.aws.elbv2 import ElasticLoadBalancingV2
from e2e.utils.cognito_bootstrap.aws.cognito import CustomDomainCognitoUserPool
from e2e.utils.cognito_bootstrap.aws.route53 import Route53HostedZone


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def delete_userpool(
    domain: str,
    userpool_name: str,
    userpool_arn: str,
    domain_alias: str,
    domain_cert_arn: str,
    region: str,
) -> None:
    userpool_domain = "auth." + domain
    userpool_id = userpool_arn.split("/")[-1]
    userpool_cloudfront_alias = domain_alias
    cognito_userpool = CustomDomainCognitoUserPool(
        userpool_name=userpool_name,
        userpool_domain=userpool_domain,
        userpool_id=userpool_id,
        domain_cert_arn=domain_cert_arn,
        region=region,
    )
    try:
        if userpool_cloudfront_alias:
            cognito_userpool.delete_userpool_domain()
        cognito_userpool.delete_userpool()
    except Exception:
        pass


def delete_cert(acm_certificate):
    try:
        acm_certificate.delete()
    except Exception:
        pass


def clean_root_domain(domain_name, hosted_zone_id, subdomain_hosted_zone):
    root_hosted_zone = Route53HostedZone(
        domain=domain_name,
        id=hosted_zone_id,
    )

    try:
        # delete the subdomain entry from the root domain
        subdomain_NS_record = subdomain_hosted_zone.generate_change_record(
            record_name=subdomain_hosted_zone.domain,
            record_type="NS",
            record_value=subdomain_hosted_zone.get_name_servers(),
            action="DELETE",
        )
        root_hosted_zone.change_record_set([subdomain_NS_record])
    except Exception:
        pass


def delete_alb(dns: str, region: str):
    try:
        alb = ElasticLoadBalancingV2(dns=dns, region=region)
        alb.delete()
    except Exception:
        pass


def delete_cognito_dependency_resources(cfg: dict):
    deployment_region = cfg["kubeflow"]["region"]
    subdomain_hosted_zone_id = cfg["route53"]["subDomain"].get("hostedZoneId", None)
    root_domain_hosted_zone_id = cfg["route53"]["rootDomain"].get("hostedZoneId", None)

    subdomain_hosted_zone = None
    root_hosted_zone = None

    if subdomain_hosted_zone_id:
        subdomain_name = cfg["route53"]["subDomain"]["name"]
        subdomain_hosted_zone = Route53HostedZone(
            domain=subdomain_name,
            id=subdomain_hosted_zone_id,
        )

        if root_domain_hosted_zone_id:
            clean_root_domain(
                domain_name=cfg["route53"]["rootDomain"]["name"],
                hosted_zone_id=root_domain_hosted_zone_id,
                subdomain_hosted_zone=subdomain_hosted_zone,
            )
            root_cert_arn = cfg["route53"]["rootDomain"].get("certARN", None)
            if root_cert_arn:
                delete_cert(acm_certificate=AcmCertificate(arn=root_cert_arn))

        subdomain_cert_deployment_region = subdomain_cert_n_virginia = None
        subdomain_cert_deployment_region_arn = cfg["route53"]["subDomain"].get(
            deployment_region + "-certARN", None
        )
        subdomain_cert_n_virginia_arn = cfg["route53"]["subDomain"].get(
            "us-east-1-certARN", None
        )
        if subdomain_cert_n_virginia_arn:
            subdomain_cert_deployment_region = (
                subdomain_cert_n_virginia
            ) = AcmCertificate(arn=subdomain_cert_n_virginia_arn)
        if deployment_region != "us-east-1" and subdomain_cert_deployment_region_arn:
            subdomain_cert_deployment_region = AcmCertificate(
                arn=subdomain_cert_deployment_region_arn, region=deployment_region
            )

        # delete userpool domain and userpool
        cognito_userpool_arn = cfg["cognitoUserpool"].get("ARN", None)
        if cognito_userpool_arn and subdomain_cert_deployment_region:
            delete_userpool(
                domain=subdomain_name,
                userpool_name=cfg["cognitoUserpool"]["name"],
                userpool_arn=cognito_userpool_arn,
                domain_alias=cfg["cognitoUserpool"]["domainAliasTarget"],
                domain_cert_arn=subdomain_cert_deployment_region.arn,
                region=deployment_region,
            )

        # delete ALB
        alb_dns = cfg["kubeflow"].get("ALBDNS", None)
        if alb_dns:
            delete_alb(alb_dns, deployment_region)

        # delete subdomain certs
        if deployment_region != "us-east-1":
            delete_cert(acm_certificate=subdomain_cert_deployment_region)
        delete_cert(acm_certificate=subdomain_cert_n_virginia)

        # delete hosted zone
        subdomain_hosted_zone.delete_hosted_zone()


if __name__ == "__main__":
    utils.print_banner("Reading Config")
    cfg = utils.load_cfg()
    delete_cognito_dependency_resources(cfg)
