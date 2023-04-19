provider "aws" {
  alias = "aws"
}

provider "aws" {
  alias = "virginia"
}

# Add a custom domain to the user pool
data "aws_route53_zone" "platform" {
  name = var.aws_route53_subdomain_zone_name
}

# In order to use a custom domain, its root(i.e. platform.example.com) must have an valid A type record
resource "aws_route53_record" "pre_cognito_domain_a_record" {
  allow_overwrite = true
  zone_id         = data.aws_route53_zone.platform.zone_id
  name            = data.aws_route53_zone.platform.name
  type            = "A"
  ttl             = "300"
  # This record will be updated after ALB creation
  records = ["127.0.0.1"]

  lifecycle {
    ignore_changes = [records, alias, ttl]
  }
}

resource "aws_acm_certificate" "cognito_domain_cert" {
  domain_name       = "*.${data.aws_route53_zone.platform.name}"
  validation_method = "DNS"
  tags              = var.tags

  lifecycle {
    create_before_destroy = true
  }

  provider = aws.virginia
}

# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/acm_certificate_validation
resource "aws_route53_record" "certificate_validation_cognito_domain" {
  for_each = {
    for dvo in aws_acm_certificate.cognito_domain_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = data.aws_route53_zone.platform.zone_id
}

resource "aws_acm_certificate_validation" "cognito_domain" {
  provider                = aws.virginia
  certificate_arn         = aws_acm_certificate.cognito_domain_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation_cognito_domain : record.fqdn]
}

resource "aws_cognito_user_pool_domain" "platform" {
  domain          = "auth.${data.aws_route53_zone.platform.name}"
  certificate_arn = aws_acm_certificate.cognito_domain_cert.arn
  user_pool_id    = aws_cognito_user_pool.platform.id

  depends_on = [
    aws_route53_record.pre_cognito_domain_a_record
  ]
}

resource "aws_route53_record" "auth_cognito_domain_record" {
  allow_overwrite = true
  name            = aws_cognito_user_pool_domain.platform.domain
  type            = "A"
  zone_id         = data.aws_route53_zone.platform.zone_id
  alias {
    evaluate_target_health = false
    name                   = aws_cognito_user_pool_domain.platform.cloudfront_distribution_arn
    # For creating an alias record to other AWS resource, route53 needs hosted zone id and DNS name.
    # Since CloudFront is a global service, there is only one hosted zone id
    # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-aliastarget.html
    zone_id = "Z2FDTNDATAQYW2"
  }
}