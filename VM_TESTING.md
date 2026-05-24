# VM Testing Guide

## Install Docker And Compose

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
docker compose version
```

## Clone And Configure

```bash
git clone <repo-url> KubeSageAI
cd KubeSageAI
cp .env.example .env
nano .env
```

For end-to-end Entra ID testing on an Azure VM, point a DNS name at the VM public IP and use HTTPS via `docker-compose.prod.yml`.

Set Microsoft Entra ID values:

```env
AZURE_TENANT_ID=e273e7a6-0676-4113-8575-ca2b6f3dd2ad
AZURE_CLIENT_ID=a6ae8259-84e5-41c3-9508-ef065a12f123
AZURE_CLIENT_SECRET=<client-secret-in-untracked-env-only>
AZURE_REDIRECT_URI=https://kubesage.nexaflow.site/auth/callback
FRONTEND_URL=https://kubesage.nexaflow.site
BACKEND_URL=https://kubesage.nexaflow.site
NEXT_PUBLIC_API_URL=https://kubesage.nexaflow.site
CORS_ORIGINS=["https://kubesage.nexaflow.site"]
DOMAIN=kubesage.nexaflow.site
ACME_EMAIL=admin@example.com
```

Set OpenAI and secrets:

```env
OPENAI_API_KEY=<openai-api-key>
OPENAI_MODEL=gpt-4.1-mini
JWT_SECRET=<long-random-secret>
ENCRYPTION_KEY=<fernet-key>
```

Generate a Fernet key:

```bash
docker run --rm python:3.12-slim sh -c "pip install cryptography >/dev/null && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
```

## Run

```bash
docker compose -f docker-compose.prod.yml up --build
```

Expected public endpoint:

- App: `https://kubesage.nexaflow.site`

## Health Checks

```bash
curl https://kubesage.nexaflow.site/health
curl https://kubesage.nexaflow.site/health/database
curl https://kubesage.nexaflow.site/health/redis
curl https://kubesage.nexaflow.site/health/azure
curl https://kubesage.nexaflow.site/health/openai
```

## Functional Test

1. Open `https://kubesage.nexaflow.site/login`.
2. Click Azure login and complete Microsoft Entra ID sign-in.
3. Confirm redirect to `https://kubesage.nexaflow.site/dashboard`.
4. Open `Subscriptions` and verify real Azure subscriptions load.
5. Select a subscription and verify real AKS clusters load.
6. Open `Clusters` and confirm discovered clusters are persisted.
7. Open `Analysis`, select a cluster, and run a scan.
8. Confirm live events appear in the activity panel.
9. Confirm incidents are created only from Kubernetes API signals.
10. Trigger AI analysis and verify structured severity, summary, root cause, timeline, and remediation suggestions.
11. Approve a remediation action.
12. Execute the approved remediation and verify the audit log entry.
13. Open `Audit Logs` and confirm login, Azure, scan, analysis, approval, and execution events are recorded.

## Troubleshooting

- `azure_subscription_list_failed`: the user lacks Azure subscription read access.
- `aks_cluster_list_failed`: Azure RBAC does not allow `Microsoft.ContainerService` reads.
- `aks_credentials_denied`: the user cannot request AKS user credentials.
- `kubernetes_scan_failed`: Kubernetes RBAC does not allow required reads.
- `openai_request_failed`: check `OPENAI_API_KEY`, outbound networking, and model access.
