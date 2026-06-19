# husk-daemon

The Husk daemon runs inside each sandbox container and exposes the
**toolbox HTTP API** that Agents and SDKs talk to.

This is the **MIT-licensed reimplementation** that, starting with Husk v0.5,
replaces the upstream Daytona daemon (AGPL-3.0) — see top-level NOTICE.

## Endpoints

```
GET  /version                  daemon identity
GET  /work-dir                 default working directory
GET  /project-dir              alias of /work-dir
GET  /user-home-dir            $HOME of the daemon process

GET  /files?path=...           list directory contents
GET  /files/info?path=...      stat a single file
GET  /files/download?path=...  stream file body (Content-Disposition)
POST /files/upload             multipart upload (path, file)
POST /files/folder             mkdir -p {path, mode?}
DELETE /files?path=...&recursive=true  rm

POST /process/execute          shell command (sync) {command, args?, cwd?, env?, timeout?}
POST /process/code-run         python/bash code (sync) {code, language?, timeout?}
```

These are the **most-used 13 endpoints** of the upstream daemon's 80.
LSP, PTY, persistent interpreter sessions, computer-use, and recordings
land in a follow-up milestone.

## Build

```bash
cd daemon
go build -ldflags="-s -w" -o ../embedded/daemon-amd64 ./cmd/daemon
GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o ../embedded/daemon-arm64 ./cmd/daemon
```

## Run

Inside a container, with /workspace as the default cwd:

```bash
/opt/husk/daemon serve --port 8080
```

## License

MIT. See ../LICENSE.
