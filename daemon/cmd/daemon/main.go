// Husk daemon — runs inside each sandbox container, exposes the toolbox API.
package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"github.com/husklabs/husk-daemon/internal/server"
)

const Version = "0.0.1"

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(2)
	}

	cmd := os.Args[1]
	args := os.Args[2:]

	switch cmd {
	case "version", "-v", "--version":
		fmt.Printf("husk-daemon %s\n", Version)
	case "serve":
		fs := flag.NewFlagSet("serve", flag.ExitOnError)
		port := fs.Int("port", 8080, "HTTP listen port")
		host := fs.String("host", "0.0.0.0", "HTTP listen host")
		_ = fs.Parse(args)

		addr := fmt.Sprintf("%s:%d", *host, *port)
		log.Printf("husk-daemon %s listening on %s", Version, addr)
		srv := server.New(Version)
		if err := http.ListenAndServe(addr, srv); err != nil {
			log.Fatal(err)
		}
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %s\n", cmd)
		printUsage()
		os.Exit(2)
	}
}

func printUsage() {
	fmt.Fprintf(os.Stderr, `husk-daemon — toolbox API server for Husk sandboxes

Usage:
  husk-daemon serve [--host 0.0.0.0] [--port 8080]
  husk-daemon version
`)
}
