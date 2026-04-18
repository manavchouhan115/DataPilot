module "irsa_extractor" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.20"

  role_name = "${local.name_prefix}-extractor-role"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["default:extractor-sa"]
    }
  }

  role_policy_arns = {
    s3_readonly = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  }
}
