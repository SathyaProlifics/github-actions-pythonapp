terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------- Data Sources ----------

data "aws_vpc" "default" {
  default = true
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# ---------- SSH Key Pair ----------

resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "ec2_key" {
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.ec2_key.public_key_openssh
}

resource "local_sensitive_file" "private_key" {
  content         = tls_private_key.ec2_key.private_key_pem
  filename        = "${path.module}/ec2_key.pem"
  file_permission = "0600"
}

# ---------- Security Group ----------

resource "aws_security_group" "ec2_dashboard" {
  name        = "${var.project_name}-sg"
  description = "Security group for EC2 Dashboard"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  ingress {
    description = "Flask App"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
  }
}

# ---------- EC2 Instance ----------

resource "aws_instance" "ec2_dashboard" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.ec2_key.key_name
  vpc_security_group_ids = [aws_security_group.ec2_dashboard.id]

  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Install dependencies
    dnf install -y git python3 python3-pip

    # Clone repository
    cd /home/ec2-user
    rm -rf ec2-dashboard
    git clone ${var.git_repo_url} ec2-dashboard
    chown -R ec2-user:ec2-user ec2-dashboard

    # Set up Python venv and install dependencies
    cd ec2-dashboard
    sudo -u ec2-user python3 -m venv venv
    sudo -u ec2-user bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

    # Configure systemd service
    cp ec2-dashboard.service /etc/systemd/system/ec2-dashboard.service
    systemctl daemon-reload
    systemctl enable ec2-dashboard
    systemctl start ec2-dashboard
  EOF

  tags = {
    Name    = "${var.project_name}-${formatdate("YYYYMMDD", timestamp())}"
    Project = var.project_name
  }

  lifecycle {
    ignore_changes = [tags["Name"]]
  }
}
