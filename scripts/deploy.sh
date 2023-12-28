#!/bin/bash

# Set the environmental variables
ENV_VARS=""
ENV_VARS="$ENV_VARS,ENVIRONMENT=Production"
ENV_VARS="$ENV_VARS,AZURE_CLIENT_ID=$AZURE_CLIENT_ID"
ENV_VARS="$ENV_VARS,AZURE_TENANT_ID=$AZURE_TENANT_ID"
ENV_VARS="$ENV_VARS,AZURE_CLIENT_SECRET=$AZURE_CLIENT_SECRET"
ENV_VARS="$ENV_VARS,AZURE_KEY_VAULT_URL=$AZURE_KEY_VAULT_URL"

# Set the command to start the microservice
command="source <(curl -s https://raw.githubusercontent.com/kontinuum-investments/Central-Finite-Curve/production/citadel/scripts/library.sh) && \
  deploy_container $DOCKERHUB_USERNAME/$DOCKERHUB_REPOSITORY:latest $CONTAINER_PORT $HOST_PORT $ENV_VARS"

# SSH into the Citadel
temp_key_file=$(mktemp)
echo "$CITADEL_SSH_PRIVATE_KEY" > "$temp_key_file"
chmod 400 "$temp_key_file"
ssh -o StrictHostKeyChecking=no -i "$temp_key_file" "$CITADEL_USERNAME"@"$CITADEL_HOST_NAME" "$command"