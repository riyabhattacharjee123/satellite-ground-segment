# Running the ground segment on AWS

Work in progress. This Terraform sets up a private home for the ground segment on AWS. Nothing is open to the internet: I reach Grafana, Airflow and the host itself over Tailscale.

## What it creates

- A VPC with a public subnet (only the NAT gateway) and a private subnet (the host, no public IP)
- A security group with no inbound rules and only the outbound ports the host needs (80, 443, and Tailscale's 41641/udp and 3478/udp)
- An S3 gateway endpoint, so S3 traffic does not go through the NAT gateway
- One Ubuntu 24.04 host with an encrypted disk and IMDSv2 only. On first boot it installs Docker and Tailscale, joins the tailnet and clones this repository
- An IAM role for the host that can only use its own S3 bucket, its own KMS key and one SSM parameter
- An S3 bucket for telemetry archives, encrypted with a KMS key that rotates every year, versioned, and closed to the public and to plain HTTP
- A CloudTrail trail with log file validation, writing to a separate bucket. It also records every read and write on the telemetry bucket

## Before you start

1. Create a reusable auth key in the Tailscale admin console (Settings, Keys). Tagging it is a good idea.
2. Store it in SSM Parameter Store. Doing this by hand keeps the key out of Terraform state:

```bash
aws ssm put-parameter --region eu-central-1 \
  --name /ground-segment/tailscale-auth-key \
  --type SecureString \
  --value "tskey-auth-..."
```

## Deploy

```bash
cd infra/aws
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

After a few minutes the host shows up in Tailscale as `ground-segment`. Then:

```bash
tailscale ssh ubuntu@ground-segment
cd /opt/satellite-ground-segment/swarm-constellation
```

From there, generate the training baseline and sensor map and start the stack as described in the main README. Grafana is then at `http://ground-segment:3000`, only from devices on your tailnet.

## Cost

The NAT gateway and a t3.large cost a few dollars a day while they run, so I tear everything down when I am not using it:

```bash
terraform destroy
```

The two S3 buckets are not force-deleted. Empty them first (including old versions in the telemetry bucket), otherwise `destroy` stops there.

## Next steps

- Start the stack automatically on first boot
- Archive the anomaly payloads to the telemetry bucket
- Keep Terraform state in S3 with locking instead of on my laptop
