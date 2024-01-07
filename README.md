# Vita-API
API for Personal Automation

[![codecov](https://codecov.io/gh/kontinuum-investments/Vita-API/branch/development/graph/badge.svg?token=K4QABJ2VQ6)](https://codecov.io/gh/kontinuum-investments/Vita-API)

# Setup
## Discord
1. Create the discord server
2. Add the bot to the server (follow instructions on [Aorta Sirius SDK](https://github.com/kontinuum-investments/Aorta-Sirius))
3. Add the respective household finances accounts to the `household-finances` channel

# How to deploy
1. Follow instructions for [Aorta Sirius SDK](https://github.com/kontinuum-investments/Aorta-Sirius)
2. Deploy the `Citadel` ([documentation](https://github.com/kontinuum-investments/Central-Finite-Curve/tree/production/citadel#readme)) which will automatically deploy this API
3. Add the key vault secrets

## Necessary Key Vault Secrets
- `MONTHLY-FINANCES-EXCEL-FILE-LINK`: Monthly Finances Excel File OneDrive Link

# Additional Resources
## Azure
- [Use the Azure login action with OpenID Connect](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal)
- [Register an application with Azure AD and create a service principal](https://learn.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#register-an-application-with-azure-ad-and-create-a-service-principal)
- Role: `Contributor`
- `App Registration` -> `[Application]` -> `Certificates & Secrets` -> `Federated Credentials` -> `Add Credentials` -> `GitHub Actions deploying Azure resources`