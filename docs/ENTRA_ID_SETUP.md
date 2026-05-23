# Microsoft Entra ID Setup

Use this when `DEMO_MODE=false`.

## App Registration

1. Open Azure Portal: https://portal.azure.com
2. Go to `Microsoft Entra ID`.
3. Open `App registrations`.
4. Select `New registration`.
5. Name: `KubeSage AI`.
6. Supported account types:
   - Internal company app: `Accounts in this organizational directory only`
   - SaaS-style testing across tenants: `Accounts in any organizational directory`
7. Platform: `Web`.
8. Redirect URI:
   - Local tunnel test: `http://localhost:8000/api/auth/azure/callback`
   - VM public IP with plain HTTP: not recommended and generally invalid for real Entra OAuth
   - Production recommended: `https://YOUR_DOMAIN/api/auth/azure/callback`

Microsoft Entra redirect URIs must match exactly. Public redirect URIs should use HTTPS; localhost is the normal HTTP exception for development.

## Client Secret

1. Open the app registration.
2. Go to `Certificates & secrets`.
3. Select `New client secret`.
4. Copy the secret value immediately.

## API Permissions

Add delegated permissions:

- Microsoft Graph: `openid`, `profile`, `email`, `offline_access`
- Azure Service Management: `user_impersonation`

Grant admin consent if your tenant requires it.

## Azure RBAC For AKS Discovery

The app registration creates a service principal. Assign it at subscription or resource group scope:

- `Reader` to list AKS clusters
- `Azure Kubernetes Service Cluster User Role` to fetch AKS user credentials

For actual Kubernetes API reads, also ensure the resulting AKS user credentials can list:

- pods
- events
- deployments
- ingresses
- pod logs

## Required Environment

```bash
DEMO_MODE=false
AZURE_CLIENT_ID=<application-client-id>
AZURE_CLIENT_SECRET=<client-secret-value>
AZURE_TENANT_ID=<directory-tenant-id>
AZURE_REDIRECT_URI=http://localhost:8000/api/auth/azure/callback
```

For safer local OAuth testing against a VM, create an SSH tunnel and use localhost URLs:

```bash
ssh -L 3000:localhost:3000 -L 8000:localhost:8000 azureuser@VM_PUBLIC_IP
```

Then set:

```bash
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]
AZURE_REDIRECT_URI=http://localhost:8000/api/auth/azure/callback
```

For real Entra login from a public endpoint, use a DNS name and HTTPS reverse proxy, then set:

```bash
FRONTEND_URL=https://YOUR_DOMAIN
BACKEND_URL=https://YOUR_DOMAIN
NEXT_PUBLIC_API_URL=https://YOUR_DOMAIN
CORS_ORIGINS=["https://YOUR_DOMAIN"]
AZURE_REDIRECT_URI=https://YOUR_DOMAIN/api/auth/azure/callback
```

With the included Nginx proxy on plain HTTP for VM-only smoke testing:

```bash
FRONTEND_URL=http://VM_PUBLIC_IP
BACKEND_URL=http://VM_PUBLIC_IP
NEXT_PUBLIC_API_URL=same-origin
CORS_ORIGINS=["http://VM_PUBLIC_IP"]
AZURE_REDIRECT_URI=http://VM_PUBLIC_IP/api/auth/azure/callback
```
