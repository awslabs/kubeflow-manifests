data "aws_route53_zone" "root" {
  name = var.aws_route53_root_zone_name
}

resource "aws_route53_zone" "platform" {
  name = var.aws_route53_subdomain_zone_name

  tags = {
    Platform = "kubeflow-on-aws"
  }

  depends_on = [
    data.aws_route53_zone.root
  ]
}

resource "aws_route53_record" "subdomain_ns_in_root" {
  zone_id = data.aws_route53_zone.root.zone_id
  name    = aws_route53_zone.platform.name
  type    = "NS"
  ttl     = "30"
  records = aws_route53_zone.platform.name_servers
}