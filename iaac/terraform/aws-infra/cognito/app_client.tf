resource "aws_cognito_user_pool_client" "platform" {
  name            = "kubeflow"
  user_pool_id    = aws_cognito_user_pool.platform.id
  generate_secret = true

  callback_urls = ["https://kubeflow.${data.aws_route53_zone.platform.name}/oauth2/idpresponse"]
  logout_urls   = ["https://kubeflow.${data.aws_route53_zone.platform.name}"]

  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile", "aws.cognito.signin.user.admin"]
  supported_identity_providers         = ["COGNITO"]
}