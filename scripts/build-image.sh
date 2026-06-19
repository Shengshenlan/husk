#!/usr/bin/env bash
# Build the husk:dev Docker image locally.
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -t husk:dev -f docker/Dockerfile .
echo "✓ image built: husk:dev"
