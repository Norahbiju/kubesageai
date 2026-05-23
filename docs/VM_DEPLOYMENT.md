# Ubuntu VM Deployment

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
sudo ufw --force enable
sudo ufw status
```

Also allow inbound TCP `80` in the Azure VM Network Security Group.

## Clone And Configure

```bash
git clone <YOUR_REPO_URL> kubesageai
cd kubesageai
cp .env.example .env
nano .env
```

For direct VM public IP access through the included Nginx reverse proxy:

```bash
PUBLIC_PORT=80
FRONTEND_URL=http://VM_PUBLIC_IP
BACKEND_URL=http://VM_PUBLIC_IP
NEXT_PUBLIC_API_URL=same-origin
CORS_ORIGINS=["http://VM_PUBLIC_IP"]
AZURE_REDIRECT_URI=http://VM_PUBLIC_IP/api/auth/azure/callback
```

## Start

```bash
docker compose down
docker compose up --build
```

Detached:

```bash
docker compose up --build -d
```

## Verify

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f web
curl http://localhost/health
curl http://localhost/health/azure
curl http://localhost/health/openai
```

Public URLs:

```text
http://VM_PUBLIC_IP
http://VM_PUBLIC_IP/docs
http://VM_PUBLIC_IP/health
```

## Rebuild After Env Changes

Next.js public environment variables are baked at build time.

```bash
docker compose down
docker compose build --no-cache web api
docker compose up
```
