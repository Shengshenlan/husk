# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Initial project scaffold (feature-first FastAPI layout, 8 business domains)
- React + Vite frontend skeleton (Phase 1.5 placeholder)
- SDK packages stubbed for Python, TypeScript, Go (Phase 1.7 placeholder)
- Docker multi-stage build, compose example/dev files
- GitHub Actions: test / integration / build / release
- alembic initial migration covering 5 tables (sandbox, snapshot, volume, api_key, preview_token)
- Smoke test suite (7 tests, all passing)

### License
- Project source code: MIT
- Phase 1 runtime: embeds upstream Daytona daemon binary (AGPL-3.0); see NOTICE
