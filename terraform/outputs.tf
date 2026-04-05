output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.ec2_dashboard.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.ec2_dashboard.public_ip
}

output "application_url" {
  description = "URL to access the EC2 Dashboard"
  value       = "http://${aws_instance.ec2_dashboard.public_ip}:5000"
}

output "ami_id" {
  description = "AMI ID used for the EC2 instance"
  value       = data.aws_ami.amazon_linux_2023.id
}

output "security_group_id" {
  description = "Security Group ID"
  value       = aws_security_group.ec2_dashboard.id
}

output "ssh_private_key_file" {
  description = "Path to the generated SSH private key"
  value       = local_sensitive_file.private_key.filename
}

output "ssh_command" {
  description = "SSH command to connect to the instance"
  value       = "ssh -i ${local_sensitive_file.private_key.filename} ec2-user@${aws_instance.ec2_dashboard.public_ip}"
}
