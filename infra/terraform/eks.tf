module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "${local.name_prefix}-cluster"
  cluster_version = "1.31"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    datapilot_nodes = {
      min_size     = 1
      max_size     = 3
      desired_size = 2
      instance_types = ["t3.medium"]
    }
  }

  manage_aws_auth_configmap = true
}
