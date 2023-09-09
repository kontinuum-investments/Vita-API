# Vita-API

API for Personal Automation

[![codecov](https://codecov.io/gh/kontinuum-investments/Vita-API/branch/development/graph/badge.svg?token=K4QABJ2VQ6)](https://codecov.io/gh/kontinuum-investments/Vita-API)

# Installation

## Aorta Sirius SDK

- Follow instructions for [Aorta Sirius SDK](https://github.com/kontinuum-investments/Aorta-Sirius)

# Development

## Aorta Sirius SDK

- Follow instructions for [Aorta Sirius SDK](https://github.com/kontinuum-investments/Aorta-Sirius)

# Additional Resources

## Azure

- [Use the Azure login action with OpenID Connect](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal)
- [Register an application with Azure AD and create a service principal](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#register-an-application-with-azure-ad-and-create-a-service-principal)
- Role: `Contributor`
- `App Registration` -> `[Application]` -> `Certificates & Secrets` -> `Federated Credentials` -> `Add Credentials` -> `GitHub Actions deploying Azure resources`

# Deployment

## Azure

1. Create a new Azure subscription
2. Create a resource group under the subscription
3. Create a container app under the resource group
    4. Set the repository metadata, do not use the quickstart image
    5. Set up `Application Ingress`
        6. Target Port: `443`
4. Setup Azure OpenID Connect with GitHub Actions (see above)
    7. Setup environment specific secrets and variables
5. Go to `Create and deploy new revision` and set the container name and the appropriate number of replicas