# KubeSage AI Testing Guide

## Connectivity

```bash
curl http://VM_PUBLIC_IP/health
curl http://VM_PUBLIC_IP/health/azure
curl http://VM_PUBLIC_IP/health/openai
curl http://VM_PUBLIC_IP/api/azure/clusters
```

## Authentication

1. Open `http://VM_PUBLIC_IP/login`.
2. Click `Login with Azure`.
3. Complete Microsoft login.
4. Expected redirect: `http://VM_PUBLIC_IP/dashboard`.
5. Browser local storage should contain `kubesage_token`.

## AKS Discovery

1. Go to `Clusters`.
2. Expected: AKS clusters from subscriptions available to the configured Entra app service principal.
3. If empty, verify RBAC:
   - `Reader`
   - `Azure Kubernetes Service Cluster User Role`

## SSE Streaming

1. Select a cluster.
2. Go to `Analysis`.
3. Expected live progress:
   - Connecting to Azure
   - Fetching AKS clusters
   - Analyzing Kubernetes events
   - Detecting deployment failures
   - Generating AI remediation
   - Preparing incident timeline
4. Expected final output: severity, summary, root cause, remediation, confidence score.

## Docker Networking

From the VM:

```bash
docker compose exec web wget -qO- http://api:8000/health || true
docker compose exec api python -c "import urllib.request; print(urllib.request.urlopen('https://api.openai.com', timeout=5).status)"
```

From your workstation:

```text
http://VM_PUBLIC_IP
http://VM_PUBLIC_IP/health
```

## Logs

```bash
docker compose logs -f api
docker compose logs -f web
```
