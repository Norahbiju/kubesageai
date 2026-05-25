# KubeSage AI Setup

## Microsoft Entra ID

1. Go to Azure Portal: `https://portal.azure.com`.
2. Open `Microsoft Entra ID`.
3. Open `App registrations`.
4. Select `New registration`.
5. Name the app `KubeSage AI`.
6. Select `Accounts in any organizational directory` for delegated SaaS-style user access.
7. Add a `Web` redirect URI.
8. Local redirect URI: `http://localhost:8000/api/auth/callback`.
9. VM redirect URI: `https://kubesage.nexaflow.site/api/auth/callback`.
10. Open `Certificates & secrets`.
11. Create a new client secret and copy the secret value immediately.
12. Copy the tenant ID from the directory overview.
13. Copy the client ID from the app registration overview.
14. Add delegated API permissions:
    - Microsoft Graph: `User.Read`
    - Azure Service Management: `user_impersonation`
15. Grant admin consent if your tenant requires it.

## Azure RBAC

The signed-in user must be able to read subscriptions and AKS metadata. For AKS access, the user also needs permission to request cluster user credentials and Kubernetes RBAC permissions for namespaces, pods, deployments, services, ingresses, events, and pod logs.

Useful Azure roles:

- `Reader` at subscription or resource group scope
- `Azure Kubernetes Service Cluster User Role` on the AKS cluster

KubeSage fails with explicit errors when Azure or Kubernetes permissions are missing.

## Environment

Copy `.env.example` to `.env` and set real values:

```env
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
AZURE_TENANT_ID=organizations
AZURE_AUTHORITY=https://login.microsoftonline.com/organizations
AZURE_CLIENT_ID=<client-id>
AZURE_CLIENT_SECRET=<client-secret-in-untracked-env-only>
AZURE_REDIRECT_URI=http://localhost:8000/api/auth/callback
AZURE_SCOPES=openid profile email offline_access https://management.azure.com/user_impersonation
OPENAI_API_KEY=<openai-api-key>
JWT_SECRET=<long-random-secret>
ENCRYPTION_KEY=<fernet-key>
```

Do not commit `AZURE_CLIENT_SECRET`. Put it only in the VM's `.env` file.

Generate `ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

For a VM, use a DNS name with HTTPS. Public HTTP redirect URIs are not reliable for Microsoft Entra web apps; `http://localhost` is the development exception.

```env
FRONTEND_URL=https://kubesage.nexaflow.site
BACKEND_URL=https://kubesage.nexaflow.site
NEXT_PUBLIC_API_URL=https://kubesage.nexaflow.site
AZURE_REDIRECT_URI=https://kubesage.nexaflow.site/api/auth/callback
CORS_ORIGINS=["https://kubesage.nexaflow.site"]
```

Restart Docker Compose after environment changes:

```bash
docker compose down
docker compose up --build
```

Test local login at `http://localhost:3000/login` or VM login at `https://kubesage.nexaflow.site/login`.
