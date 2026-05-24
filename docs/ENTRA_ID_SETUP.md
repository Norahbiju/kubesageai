# Microsoft Entra ID Setup

Use the root [SETUP.md](../SETUP.md) for the current KubeSage AI Entra ID configuration.

Current callback URLs:

- Local: `http://localhost:8000/auth/callback`
- VM: `https://kubesage.nexaflow.site/auth/callback`

The application uses Microsoft identity platform authorization code flow, validates the Azure ID token signature, stores encrypted delegated Azure tokens, and exposes the browser only to `api-gateway`.
