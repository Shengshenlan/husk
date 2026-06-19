#!/usr/bin/env bash
# Pull the upstream Daytona daemon image and extract the daemon binary
# for amd64 and arm64. Outputs to ./embedded/.
#
# This is intentionally a thin wrapper script — Phase 1 depends on the
# upstream AGPL daemon binary, embedded as a runtime artifact only.
# See NOTICE for the licensing rationale.

set -euo pipefail

UPSTREAM_IMAGE="${UPSTREAM_DAEMON_IMAGE:-daytonaio/daemon:latest}"
OUT_DIR="${1:-embedded}"
DAEMON_PATH_IN_IMAGE="${DAEMON_PATH_IN_IMAGE:-/usr/local/bin/daemon}"

mkdir -p "$OUT_DIR"

for arch in amd64 arm64; do
  echo "→ pulling $UPSTREAM_IMAGE ($arch)"
  docker pull --platform "linux/$arch" "$UPSTREAM_IMAGE"
  cid=$(docker create --platform "linux/$arch" "$UPSTREAM_IMAGE")
  docker cp "$cid:$DAEMON_PATH_IN_IMAGE" "$OUT_DIR/daemon-$arch"
  docker rm "$cid" >/dev/null
  chmod +x "$OUT_DIR/daemon-$arch"
  echo "  wrote $OUT_DIR/daemon-$arch"
done

echo "✓ embedded/ ready"
