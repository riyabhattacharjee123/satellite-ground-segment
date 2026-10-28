output "instance_id" {
  value = aws_instance.host.id
}

output "private_ip" {
  value = aws_instance.host.private_ip
}

output "data_bucket" {
  value = aws_s3_bucket.data.id
}

output "audit_bucket" {
  value = aws_s3_bucket.audit.id
}

output "grafana_url" {
  description = "Only reachable from devices on your tailnet"
  value       = "http://${var.name}:3000"
}
