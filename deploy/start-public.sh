#!/bin/sh
set -eu

# Railway sets its public domain after Networking -> Generate Domain.
# Use the explicit HTTPS origin so browser WebSockets cannot be spoofed.
if [ -z "${PATIO_PUBLIC_ORIGIN:-}" ] && [ -n "${RAILWAY_PUBLIC_DOMAIN:-}" ]; then
  export PATIO_PUBLIC_ORIGIN="https://${RAILWAY_PUBLIC_DOMAIN}"
fi

exec python -m uvicorn app.hosted:app \
  --host 0.0.0.0 --port "${PORT:-8000}" \
  --workers 1 --no-server-header --proxy-headers \
  --forwarded-allow-ips='*' --ws-max-size 4096 --ws-max-queue 8
