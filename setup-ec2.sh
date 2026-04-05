#!/bin/bash
# EC2 Setup Script - Run this on a fresh Amazon Linux 2 / Ubuntu EC2 instance
# Ensure port 5000 is open in the Security Group (inbound TCP 5000)

set -e

echo "=== Updating system packages ==="
if command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git
elif command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git
fi

echo "=== Setting up application ==="
cd /home/ec2-user 2>/dev/null || cd /home/ubuntu
mkdir -p ec2-dashboard && cd ec2-dashboard

echo "=== Creating virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Setup complete! ==="
echo "Start the app with: source venv/bin/activate && python app.py"
echo "Access at: http://<YOUR-EC2-PUBLIC-IP>:5000"
