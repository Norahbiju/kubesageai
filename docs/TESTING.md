# Testing

Use the root [VM_TESTING.md](../VM_TESTING.md) for end-to-end validation.

Minimum local checks:

```bash
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8000/health/database
curl http://localhost:8000/health/redis
curl http://localhost:8000/health/azure
curl http://localhost:8000/health/openai
```

Then test through the frontend at `http://localhost:3000`.
