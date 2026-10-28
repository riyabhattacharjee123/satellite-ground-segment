data "aws_iam_policy_document" "assume_ec2" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "host" {
  name_prefix        = "${var.name}-host-"
  assume_role_policy = data.aws_iam_policy_document.assume_ec2.json
}

# Least privilege: the host can only use its own bucket, its own KMS key
# and the one parameter that holds the Tailscale auth key
data "aws_iam_policy_document" "host" {
  statement {
    sid       = "ListDataBucket"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.data.arn]
  }

  statement {
    sid       = "ReadWriteTelemetry"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.data.arn}/*"]
  }

  statement {
    sid       = "UseDataKey"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [aws_kms_key.data.arn]
  }

  statement {
    sid       = "ReadTailscaleKey"
    actions   = ["ssm:GetParameter"]
    resources = ["arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${var.tailscale_auth_key_parameter}"]
  }
}

resource "aws_iam_role_policy" "host" {
  name   = "least-privilege"
  role   = aws_iam_role.host.id
  policy = data.aws_iam_policy_document.host.json
}

resource "aws_iam_instance_profile" "host" {
  name_prefix = "${var.name}-host-"
  role        = aws_iam_role.host.name
}
