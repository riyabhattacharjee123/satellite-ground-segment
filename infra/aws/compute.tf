# Ubuntu 24.04 LTS, published by Canonical
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_instance" "host" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.private.id
  vpc_security_group_ids      = [aws_security_group.host.id]
  iam_instance_profile        = aws_iam_instance_profile.host.name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    aws_region          = var.aws_region
    tailscale_parameter = var.tailscale_auth_key_parameter
    hostname            = var.name
    repo_url            = var.repo_url
  })
  user_data_replace_on_change = true

  # IMDSv2 only
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
    encrypted   = true
  }

  tags = { Name = var.name }

  lifecycle {
    # A new Ubuntu image should not replace a running host
    ignore_changes = [ami]
  }

  # First boot installs packages, so the route through NAT must exist before the host starts
  depends_on = [aws_route_table_association.private]
}
