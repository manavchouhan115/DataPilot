resource "aws_s3_bucket" "data_lake" {
  bucket = "${local.name_prefix}-data-lake-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "data_lake_block" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
