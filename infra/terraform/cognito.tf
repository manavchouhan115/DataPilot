resource "aws_cognito_user_pool" "pool" {
  name = "${local.name_prefix}-user-pool"

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  password_policy {
    minimum_length = 8
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "${local.name_prefix}-app-client"
  user_pool_id = aws_cognito_user_pool.pool.id
  generate_secret = false
}
