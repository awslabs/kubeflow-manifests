import boto3
import json
import pytest

from e2e.utils.cognito_bootstrap.cognito_pre_deployment import (
    create_subdomain_hosted_zone,
    create_certificates,
    create_cognito_userpool,
)
from e2e.utils.cognito_bootstrap.common import load_cfg, write_cfg
from e2e.utils.cognito_bootstrap.cognito_pre_deployment_cleanup import (
    delete_cognito_dependency_resources,
)
from e2e.utils.cognito_bootstrap.cognito_post_deployment import (
    update_hosted_zone_with_alb,
)
from e2e.utils.config import configure_resource_fixture
from e2e.fixtures.cluster import associate_iam_oidc_provider
from e2e.utils.utils import (
    load_json_file,
    rand_name,
    wait_for,
    get_iam_client,
    get_eks_client,
    get_ec2_client,
)
from e2e.utils.config import configure_env_file
from e2e.utils.custom_resources import get_ingress


@pytest.fixture(scope="class")
def cognito_bootstrap(
    metadata, region, request, root_domain_name, root_domain_hosted_zone_id
):
    if not root_domain_name or not root_domain_hosted_zone_id:
        pytest.fail(
            "--root-domain-name and --root-domain-hosted-zone-id required for cognito related tests"
        )

    subdomain_name = rand_name("platform") + "." + root_domain_name
    cognito_deps = {"kubeflow": {"region": region}}

    def on_create():
        root_hosted_zone, subdomain_hosted_zone = create_subdomain_hosted_zone(
            subdomain_name,
            root_domain_name,
            region,
            root_domain_hosted_zone_id,
        )
        cognito_deps["route53"] = {
            "rootDomain": {
                "name": root_hosted_zone.domain,
                "hostedZoneId": root_hosted_zone.id,
            },
            "subDomain": {
                "name": subdomain_hosted_zone.domain,
                "hostedZoneId": subdomain_hosted_zone.id,
            },
        }

        (
            root_certificate,
            subdomain_cert_n_virginia,
            subdomain_cert_deployment_region,
        ) = create_certificates(region, subdomain_hosted_zone, root_hosted_zone)

        cognito_deps["route53"]["rootDomain"]["certARN"] = root_certificate.arn

        cognito_deps["route53"]["subDomain"][
            "us-east-1-certARN"
        ] = subdomain_cert_n_virginia.arn
        cognito_deps["route53"]["subDomain"][
            region + "-certARN"
        ] = subdomain_cert_deployment_region.arn

        userpool_name = subdomain_name
        cognito_userpool, _ = create_cognito_userpool(
            userpool_name,
            region,
            subdomain_hosted_zone,
            subdomain_cert_n_virginia.arn,
        )

        cognito_deps["cognitoUserpool"] = {
            "name": cognito_userpool.userpool_name,
            "ARN": cognito_userpool.arn,
            "appClientId": cognito_userpool.client_id,
            "domain": cognito_userpool.userpool_domain,
            "domainAliasTarget": cognito_userpool.cloudfront_domain,
        }

    def on_delete():
        cfg = metadata.get("cognito_dependencies") or cognito_deps
        alb_dns = metadata.get("alb_dns")
        if alb_dns:
            cfg["kubeflow"]["ALBDNS"] = alb_dns
        delete_cognito_dependency_resources(cfg)

    return configure_resource_fixture(
        metadata, request, cognito_deps, "cognito_dependencies", on_create, on_delete
    )


@pytest.fixture(scope="class")
def configure_kf_admin_role(metadata, region, request, account_id, cluster):
    role_name = rand_name("kf-admin-role")
    iam_client = get_iam_client(region)
    iam_resource = boto3.resource("iam")

    def on_create():
        associate_iam_oidc_provider(cluster, region)
        eks_client = get_eks_client(region)
        response = eks_client.describe_cluster(name=cluster)

        oidc_provider_url = response["cluster"]["identity"]["oidc"]["issuer"][8:]
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "Federated": f"arn:aws:iam::{account_id}:oidc-provider/{oidc_provider_url}"
                            },
                            "Action": "sts:AssumeRoleWithWebIdentity",
                            "Condition": {
                                "StringEquals": {
                                    f"{oidc_provider_url}:aud": "sts.amazonaws.com",
                                    f"{oidc_provider_url}:sub": [
                                        "system:serviceaccount:kubeflow:alb-ingress-controller",
                                        "system:serviceaccount:kubeflow:profiles-controller-service-account",
                                    ],
                                }
                            },
                        }
                    ],
                }
            ),
        )

        alb_role_policy = iam_resource.RolePolicy(role_name, "alb_controller_policy")
        alb_role_policy.put(
            PolicyDocument=json.dumps(
                load_json_file("../../infra_configs/iam_alb_ingress_policy.json")
            )
        )
        role_arn = response["Role"]["Arn"]
        alb_sa_filepath = "../../aws-alb-ingress-controller/base/service-account.yaml"
        alb_sa = load_cfg(alb_sa_filepath)
        alb_sa["metadata"]["annotations"] = {"eks.amazonaws.com/role-arn": role_arn}
        write_cfg(alb_sa, alb_sa_filepath)

        profile_controller_policy = iam_resource.RolePolicy(
            role_name, "profile_controller_policy"
        )
        profile_controller_policy.put(
            PolicyDocument=json.dumps(
                load_json_file("../../infra_configs/iam_profile_controller_policy.json")
            )
        )
        profile_sa_filepath = (
            "../../aws-alb-ingress-controller/base/service-account.yaml"
        )
        profile_sa = load_cfg(profile_sa_filepath)
        profile_sa["metadata"]["annotations"] = {"eks.amazonaws.com/role-arn": role_arn}
        write_cfg(profile_sa, profile_sa_filepath)

    def on_delete():
        role = metadata.get("kf-admin-role-name") or role_name
        iam_resource.RolePolicy(role, "alb_controller_policy").delete()
        iam_resource.RolePolicy(role, "profile_controller_policy").delete()
        iam_client.delete_role(RoleName=role)

    return configure_resource_fixture(
        metadata, request, role_name, "kf-admin-role-name", on_create, on_delete
    )


@pytest.fixture(scope="class")
def configure_ingress(region, cognito_bootstrap, cluster, configure_kf_admin_role):

    configure_env_file(
        env_file_path="../../../../distributions/aws/istio-ingress/overlays/cognito/params.env",
        env_dict={
            "CognitoUserPoolArn": cognito_bootstrap["cognitoUserpool"]["ARN"],
            "CognitoAppClientId": cognito_bootstrap["cognitoUserpool"]["appClientId"],
            "CognitoUserPoolDomain": cognito_bootstrap["cognitoUserpool"]["domain"],
            "certArn": cognito_bootstrap["route53"]["subDomain"][region + "-certARN"],
            "loadBalancerScheme": "internet-facing",
        },
    )

    configure_env_file(
        env_file_path="../../../../distributions/aws/aws-alb-ingress-controller/base/params.env",
        env_dict={
            "clusterName": cluster,
        },
    )

    ec2_client = get_ec2_client(region)
    response = ec2_client.describe_subnets(
        Filters=[
            {
                "Name": "tag:alpha.eksctl.io/cluster-name",
                "Values": [
                    cluster,
                ],
            },
        ]
    )

    subnets = response["Subnets"]
    resources = []
    for subnet in subnets:
        resources.append(subnet["SubnetId"])

    ec2_client.create_tags(
        Resources=resources,
        Tags=[
            {"Key": f"kubernetes.io/cluster/{cluster}", "Value": "owned"},
        ],
    )


def wait_for_alb_dns(cluster, region):
    def callback():
        ingress = get_ingress(cluster, region)

        assert ingress.get("status") is not None
        assert ingress["status"]["loadBalancer"] is not None
        assert len(ingress["status"]["loadBalancer"]["ingress"]) > 0
        assert (
            ingress["status"]["loadBalancer"]["ingress"][0].get("hostname", None)
            is not None
        )

    wait_for(callback)


@pytest.fixture(scope="class")
def post_deployment_dns_update(
    metadata, region, request, cluster, cognito_bootstrap, kustomize
):

    alb_dns = None

    def on_create():
        wait_for_alb_dns(cluster, region)
        ingress = get_ingress(cluster, region)
        alb_dns = ingress["status"]["loadBalancer"]["ingress"][0]["hostname"]
        update_hosted_zone_with_alb(
            subdomain_name=cognito_bootstrap["route53"]["subDomain"]["name"],
            subdomain_hosted_zone_id=cognito_bootstrap["route53"]["subDomain"][
                "hostedZoneId"
            ],
            alb_dns=alb_dns,
            deployment_region=region,
        )

    def on_delete():
        pass

    return configure_resource_fixture(
        metadata, request, alb_dns, "alb_dns", on_create, on_delete
    )
