variable "aws_region" {
  description = "AWS region for everything in this stack"
  type        = string
  default     = "eu-central-1"
}

variable "name" {
  description = "Prefix for resource names, also used as the Tailscale hostname"
  type        = string
  default     = "ground-segment"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Only the NAT gateway lives here"
  type        = string
  default     = "10.20.0.0/24"
}

variable "private_subnet_cidr" {
  description = "The ground segment host lives here, without a public IP"
  type        = string
  default     = "10.20.1.0/24"
}

variable "instance_type" {
  description = "The Docker Compose stack has 9 containers including Airflow, so it needs about 8 GB of memory"
  type        = string
  default     = "t3.large"
}

variable "tailscale_auth_key_parameter" {
  description = "Name of an SSM SecureString parameter that holds a Tailscale auth key. Create it by hand so the key never ends up in Terraform state."
  type        = string
  default     = "/ground-segment/tailscale-auth-key"

  validation {
    condition     = startswith(var.tailscale_auth_key_parameter, "/")
    error_message = "The parameter name must start with a slash, e.g. /ground-segment/tailscale-auth-key."
  }
}

variable "repo_url" {
  description = "Repository that is cloned onto the host"
  type        = string
  default     = "https://github.com/riyabhattacharjee123/satellite-ground-segment.git"
}
