#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting user_data setup for CPU LightGBM benchmark node"

# Set up 2GB swap to prevent OOM on t3.micro (1GB RAM)
fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

apt-get update -y
apt-get install -y python3 python3-pip

pip3 install --upgrade pip
pip3 install lightgbm scikit-learn pandas numpy kaggle

mkdir -p /home/ubuntu/ml-benchmark
chown ubuntu:ubuntu /home/ubuntu/ml-benchmark

echo "CPU environment ready: lightgbm, scikit-learn, pandas, numpy, kaggle installed system-wide."
