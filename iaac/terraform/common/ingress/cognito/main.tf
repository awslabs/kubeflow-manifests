data "aws_route53_zone" "platform" {
  name = var.aws_route53_subdomain_zone_name
}

resource "aws_acm_certificate" "deployment_region" {
  domain_name       = "*.${data.aws_route53_zone.platform.name}"
  validation_method = "DNS"
  tags              = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "certificate_validation_deployment_region" {
  for_each = {
    for dvo in aws_acm_certificate.deployment_region.domain_validation_options : dvo.domain_name => {
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

resource "aws_acm_certificate_validation" "deployment_region" {
  certificate_arn         = aws_acm_certificate.deployment_region.arn
  validation_record_fqdns = [for record in aws_route53_record.certificate_validation_deployment_region : record.fqdn]
}

# Implement ingress in terraform instead of using chart to use features like wait_for_load_balancer
resource "kubernetes_ingress_v1" "istio_ingress" {
  wait_for_load_balancer = true

  metadata {
    annotations = {
      "alb.ingress.kubernetes.io/auth-type" : "cognito",
      "alb.ingress.kubernetes.io/auth-idp-cognito" : "{\"UserPoolArn\":\"${var.cognito_user_pool_arn}\",\"UserPoolClientId\":\"${var.cognito_app_client_id}\", \"UserPoolDomain\":\"${var.cognito_user_pool_domain}\"}"
      "alb.ingress.kubernetes.io/certificate-arn" : "${aws_acm_certificate.deployment_region.arn}"
      "alb.ingress.kubernetes.io/listen-ports" : "[{\"HTTPS\":443}]",
      "alb.ingress.kubernetes.io/target-type" : "ip",
      "alb.ingress.kubernetes.io/load-balancer-attributes" : "routing.http.drop_invalid_header_fields.enabled=true",
      "alb.ingress.kubernetes.io/scheme" : "${var.load_balancer_scheme}"
      "alb.ingress.kubernetes.io/tags" : trim(trimspace(replace(replace(jsonencode(var.tags), "\"", ""), ":", "=")), "{}")
    }
    name      = "istio-ingress"
    namespace = "istio-system"
  }

  spec {
    ingress_class_name = "alb"
    rule {
      http {
        path {
          path = "/*"
          backend {
            service {
              name = "istio-ingressgateway"
              port {
                number = 80
              }
            }
          }
          path_type = "ImplementationSpecific"
        }
      }
    }
  }
}

# Import by tag because ALB cannot be imported by DNS provided by output of Ingress status
data "aws_lb" "istio_ingress" {
  tags = {
    "elbv2.k8s.aws/cluster" = var.cluster_name
    "ingress.k8s.aws/stack" = "istio-system/istio-ingress"
  }
  depends_on = [
    kubernetes_ingress_v1.istio_ingress
  ]
}

resource "aws_route53_record" "cname_record" {
  allow_overwrite = true
  zone_id         = data.aws_route53_zone.platform.zone_id
  name            = "kubeflow.${data.aws_route53_zone.platform.name}"
  type            = "CNAME"
  records         = [data.aws_lb.istio_ingress.dns_name]
  ttl             = "300"
}

resource "aws_route53_record" "a_record" {
  allow_overwrite = true
  zone_id         = data.aws_route53_zone.platform.zone_id
  name            = data.aws_route53_zone.platform.name
  type            = "A"

  alias {
    name                   = data.aws_lb.istio_ingress.dns_name
    zone_id                = data.aws_lb.istio_ingress.zone_id
    evaluate_target_health = false
  }
}