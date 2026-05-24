# VM Deployment

For HTTP VM testing, use the root [VM_TESTING.md](../VM_TESTING.md).

For HTTPS production-style deployment, configure `.env.production.example`, set `DOMAIN=kubesage.nexaflow.site`, add `ACME_EMAIL`, register `https://kubesage.nexaflow.site/auth/callback` in Microsoft Entra ID, and run:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

The production compose file runs the same microservice set as local compose, with Caddy and Nginx in front of `frontend-web` and `api-gateway`.
