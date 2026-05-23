# Ubuntu VM Deployment

This production path uses a real DNS name, HTTPS, Caddy for automatic TLS certificates, Nginx as the internal reverse proxy, and the FastAPI/Next.js containers behind it.

Microsoft Entra production redirect URIs should be HTTPS. `http://localhost/...` is fine for local development, but `http://VM_PUBLIC_IP/...` is not a production Entra setup.

## Prerequisites

- A DNS record such as `kubesage.example.com` pointing to the VM public IP.
- Azure VM Network Security Group allows inbound TCP `80`, `443`, and `22`.
- A Microsoft Entra app registration with this redirect URI:

```text
https://YOUR_DOMAIN/api/auth/azure/callback
```

## Install Docker

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg git ufw
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status
```

## Clone And Configure

```bash
git clone <YOUR_REPO_URL> kubesageai
cd kubesageai
cp .env.production.example .env
nano .env
```

Set these values to your actual domain:

```env
DOMAIN=YOUR_DOMAIN
ACME_EMAIL=YOUR_EMAIL
FRONTEND_URL=https://YOUR_DOMAIN
BACKEND_URL=https://YOUR_DOMAIN
NEXT_PUBLIC_API_URL=same-origin
CORS_ORIGINS=["https://YOUR_DOMAIN"]
AZURE_REDIRECT_URI=https://YOUR_DOMAIN/api/auth/azure/callback
```

Set Microsoft Entra credentials:

```env
DEMO_MODE=false
AZURE_CLIENT_ID=<application-client-id>
AZURE_CLIENT_SECRET=<client-secret-value>
AZURE_TENANT_ID=<directory-tenant-id>
```

Generate strong secrets:

```bash
openssl rand -hex 32
```

Use different values for `JWT_SECRET` and `NEXTAUTH_SECRET`.

## Start Production

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up --build -d
```

## Verify

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f caddy
docker compose -f docker-compose.prod.yml logs -f api
curl -I https://YOUR_DOMAIN
curl https://YOUR_DOMAIN/health
curl https://YOUR_DOMAIN/health/azure
```

Open:

```text
https://YOUR_DOMAIN
```

Then click `Login with Azure`.

## Rebuild After Env Changes

Next.js public environment variables are baked at build time.

```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build --no-cache web api
docker compose -f docker-compose.prod.yml up -d
```

## Local Or Demo HTTP

Use `.env.example` and `docker-compose.yml` only for localhost/demo HTTP runs. Do not use `http://VM_PUBLIC_IP` for production Entra login.
