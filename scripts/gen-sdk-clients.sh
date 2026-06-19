#!/usr/bin/env bash
# Regenerate all language SDK clients from the live Husk OpenAPI schema.
# Requires: a running Husk at $HUSK_URL (default http://localhost:8000),
# OR pass a path with --schema /path/to/openapi.json
set -euo pipefail

SCHEMA="${SCHEMA:-/tmp/openapi.json}"
HUSK_URL="${HUSK_URL:-http://localhost:8000}"

# If schema doesn't exist or is stale, derive it from the current code (offline path).
if [[ "$SCHEMA" == "/tmp/openapi.json" ]] && [[ ! -f "$SCHEMA" || $(find husk -newer "$SCHEMA" -type f 2>/dev/null | head -1) ]]; then
  echo "→ extracting OpenAPI schema offline from husk.main:app"
  uv run python -c "
import json
from husk.main import app
with open('$SCHEMA', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
" 2>/dev/null
fi

echo "→ source schema: $SCHEMA"

# ── Python ──
if command -v openapi-python-client >/dev/null 2>&1; then
  echo "→ regenerating sdks/python/husk_client/_generated"
  rm -rf sdks/python/husk_client/_generated sdks/python/_tmp_gen
  openapi-python-client generate --path "$SCHEMA" --output-path sdks/python/_tmp_gen --overwrite
  mv sdks/python/_tmp_gen/husk_client sdks/python/husk_client/_generated
  rm -rf sdks/python/_tmp_gen
else
  echo "  (skipped) openapi-python-client not installed: uv tool install openapi-python-client"
fi

# ── TypeScript ──
echo "→ regenerating sdks/typescript/src/_generated/schemas.ts"
npx -y openapi-typescript "$SCHEMA" -o sdks/typescript/src/_generated/schemas.ts

# ── Go (only if oapi-codegen available) ──
if command -v oapi-codegen >/dev/null 2>&1; then
  echo "→ regenerating sdks/go/client/_generated"
  oapi-codegen -package generated -generate types,client \
    -o sdks/go/client/_generated/client.gen.go "$SCHEMA"
else
  echo "  (skipped) oapi-codegen not installed (Go SDK)"
fi

echo "✓ SDK regeneration complete"
