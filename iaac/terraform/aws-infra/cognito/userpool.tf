resource "aws_cognito_user_pool" "platform" {
  name = var.cognito_user_pool_name

  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
    string_attribute_constraints {
      min_length = "1"
      max_length = "2048"
    }
  }
  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  auto_verified_attributes = ["email"]

  tags = var.tags
}