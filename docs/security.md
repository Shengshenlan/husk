# Security model

Husk is **single-tenant by design**. The threat model assumes:

- One trusted operator running Husk on their own machine or VM
- Multiple sandbox containers may be created by that operator (or via Agent)
- The sandbox **inside** is treated as untrusted (it runs arbitrary code)

## Boundaries

| Layer | Trust |
|---|---|
| Host kernel | Trusted |
| Host filesystem | Trusted (you own the box) |
| Husk control plane | Trusted (your code) |
| Sandbox container | **Untrusted** (runs Agent / user code) |
| Sandbox network egress | Optionally restricted (M4) |

## Hardening defaults (M1)

- Sandboxes start with `--cap-drop=ALL --security-opt=no-new-privileges`
- Read-only root filesystem where possible
- Resource limits (`--cpus`, `--memory`, `--pids-limit`)
- Sandbox containers labeled `husk=true` for reaper identification

## Docker socket = root

Husk requires access to the Docker socket. **Anyone with this access has
root on the host.** Recommended mitigations:

1. Run Husk on a dedicated VM
2. Use [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
3. Use a [docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) to filter API calls (Phase 3+)

## API Key handling

- Stored hashed (argon2)
- Plain text shown exactly once at creation
- Prefix `hk_` for easy log scanning
- Revocable via `husk apikey revoke <name>`

## Daemon binary integrity (Phase 1)

- The embedded upstream daemon is SHA-256 verified at image build time
- Binary checksums recorded in `embedded/CHECKSUMS`

## What's NOT in scope (yet)

- Multi-tenant isolation
- Sandbox-to-sandbox network policy beyond egress allowlists
- Hypervisor-level isolation (gVisor, Kata) — possible to plug in via Docker
  runtime config but not bundled
