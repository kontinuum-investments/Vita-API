#!/bin/bash

# Update & Upgrade
apt update
apt upgrade

# Set timezone
#sudo timedatectl set-timezone Pacific/Auckland

# Setup dependencies
apt install -y python3 python3-pip
pip3 install --no-cache-dir --upgrade -r requirements.txt
if [ "$ENVIRONMENT" == "Production" ]; then
    pip3 install aorta_sirius --no-cache-dir --upgrade
else
    pip3 install aorta_sirius-dev --no-cache-dir --upgrade
fi
