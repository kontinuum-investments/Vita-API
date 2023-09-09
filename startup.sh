#!/bin/bash
# Setup dependencies
pip install --no-cache-dir --upgrade -r requirements.txt
if [ "$ENVIRONMENT" = "Production" ]; then
    pip install aorta_sirius --no-cache-dir --upgrade
else
    pip install aorta_sirius --no-cache-dir --upgrade
fi

# Start the Uvicorn server
uvicorn main:app --host 0.0.0.0 --port 443