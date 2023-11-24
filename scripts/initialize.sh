#!/bin/bash

# Setup dependencies
apt install -y python3 python3-pip python3-venv

# Set up the virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt
if [ "$ENVIRONMENT" != "Production" ]; then
    pip3 remove aorta_sirius
    pip3 install aorta_sirius-dev
fi