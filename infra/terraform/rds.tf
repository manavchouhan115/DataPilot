module "aurora" {
  source  = "terraform-aws-modules/rds-aurora/aws"
  version = "~> 8.0"

  name           = "${local.name_prefix}-db"
  engine         = "aurora-postgresql"
  engine_version = "15.8"
  instance_class = "db.t3.medium"
  instances = {
    one = {}
  }

  vpc_id               = module.vpc.vpc_id
  subnets              = module.vpc.private_subnets
  create_db_subnet_group = true

  master_username = "datapilot_admin"
  manage_master_user_password = true

  skip_final_snapshot = true
}
