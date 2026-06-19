# husk-go

Auto-generated Go client for the [Husk](https://github.com/your-org/husk)
control plane API.

## Install

```bash
go get github.com/husklabs/husk-go
```

## Quickstart

```go
package main

import (
    "context"
    "fmt"
    "github.com/husklabs/husk-go/client"
)

func main() {
    c, _ := client.NewClient("http://localhost:8000",
        client.WithAuthToken("hk_xxxxxxxxxxxx"))

    sb, _ := c.CreateSandbox(context.Background(), client.CreateSandboxRequest{
        SnapshotID: "py-3.12", CPU: 2, MemoryMB: 2048,
    })
    fmt.Println(sb.ID, sb.State)
}
```

## Status

Phase 1.7 (M5.8 – M5.10). Currently scaffold-only.

## License

MIT
