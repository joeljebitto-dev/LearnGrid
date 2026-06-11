# API Gateway Smoke Tests

These tests validate the tracked Nginx gateway configuration and can optionally smoke-test a
running local gateway.

Run static checks:

```bash
python -m pytest tests/gateway
```

Run live checks after `pnpm dev` is running:

```bash
GATEWAY_BASE_URL=https://127.0.0.1:8443 \
GATEWAY_HTTP_URL=http://127.0.0.1:8080 \
python -m pytest tests/gateway
```
