## What

(Brief summary — what does this PR do?)

## Why

(Link issue or explain motivation.)

## How

(Implementation notes worth flagging to the reviewer.)

## Test plan

- [ ] `uv run pytest tests/unit/`
- [ ] `uv run pytest tests/integration/` (if Docker affected)
- [ ] Manual: `husk serve` + `curl /api/...`
- [ ] If schema changed: regenerated SDK clients
- [ ] If frontend changed: `cd frontend && pnpm build`
