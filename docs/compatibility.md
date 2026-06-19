# Compatibility with upstream Daytona

Husk implements a subset of the Daytona control plane API and is compatible
with the upstream SDKs at the wire level — `pip install daytona` users can
point their `base_url` at Husk and most operations work.

## What works

- Sandbox lifecycle (create / list / get / start / stop / destroy)
- Snapshot pull (image references)
- Toolbox proxy (`/api/toolbox/:id/*`)
- Preview URLs (signed)
- API Key auth (Bearer)
- Stub `/api/users/me`, `/api/organizations`, `/api/config`

## What's stubbed

| Daytona endpoint | Husk behavior |
|---|---|
| `GET /api/users/me` | Returns a single fixed user `user_default` |
| `GET /api/organizations` | Returns a single org `default` |
| `GET /api/config` | Returns single-region defaults |
| `Sandbox.organizationId` | Always `org_default` |
| `Sandbox.runnerId` / `region` | Always `default` |

## What's missing

- Multi-tenant: organizations, members, invitations, quotas
- Audit log API
- Webhook endpoints (Svix)
- Snapshot declarative builder
- Sandbox backup/restore (S3)
- Multi-runner coordination
- Computer-use endpoints (Phase 2.x at earliest)

See `../PLAN.md` §7 for the full "not in scope" list.

## Versioning

Husk pins compatibility to a specific upstream Daytona SDK version per
release. Run `tests/compat/` against the SDK version listed in `CHANGELOG.md`
to verify.
