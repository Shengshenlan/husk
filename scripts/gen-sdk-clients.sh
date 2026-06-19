#!/usr/bin/env bash
# Regenerate all language SDK clients from a running Husk control plane's OpenAPI spec.
# Requires: a running Husk at $HUSK_URL (default http://localhost:8000).

set -euo pipefail

HUSK_URL="${HUSK_URL:-http://localhost:8000}"
SCHEMA_URL="$HUSK_URL/openapi.json"

echo "→ source schema: $SCHEMA_URL"

# ── Python ──
if command -v openapi-python-client >/dev/null 2>&1; then
  echo "→ regenerating sdks/python/husk_client/_generated"
  rm -rf sdks/python/husk_client/_generated
  openapi-python-client generate \
    --url "$SCHEMA_URL" \
    --output-path sdks/python/husk_client/_generated \
    --overwrite
else
  echo "  (skipped) openapi-python-client not installed: pipx install openapi-python-client"
fi

# ── TypeScript ──
if command -v pnpm >/dev/null 2>&1; then
  echo "→ regenerating sdks/typescript/src/_generated"
  pnpm --dir sdks/typescript exec openapi-typescript "$SCHEMA_URL" \
    -o src/_generated/schemas.ts || \
    npx openapi-typescript "$SCHEMA_URL" -o sdks/typescript/src/_generated/schemas.ts
else
  echo "  (skipped) pnpm not installed"
fi

# ── Go ──
if command -v oapi-codegen >/dev/null 2>&1; then
  echo "→ regenerating sdks/go/client/_generated"
  oapi-codegen -package generated -generate types,client \
    -o sdks/go/client/_generated/client.gen.go \
    "$SCHEMA_URL"
else
  echo "  (skipped) oapi-codegen not installed: go install github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@latest"
fi

echo "✓ SDK regeneration complete"
