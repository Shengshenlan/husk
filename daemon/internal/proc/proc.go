// Package proc implements the daemon's process-execution endpoints.
package proc

import (
	"context"
	"net/http"
	"os/exec"
	"time"

	"github.com/gin-gonic/gin"
)

type execRequest struct {
	Command string   `json:"command"`
	Args    []string `json:"args,omitempty"`
	Cwd     string   `json:"cwd,omitempty"`
	Env     []string `json:"env,omitempty"`
	Timeout int      `json:"timeout,omitempty"` // seconds; 0 = no timeout
}

type execResponse struct {
	ExitCode int    `json:"exit_code"`
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	Result   string `json:"result"` // alias for stdout (upstream-compat)
}

// Execute runs a single shell command synchronously and returns combined output.
func Execute(c *gin.Context) {
	var req execRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if req.Command == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "command required"})
		return
	}

	ctx := c.Request.Context()
	if req.Timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, time.Duration(req.Timeout)*time.Second)
		defer cancel()
	}

	// Run via /bin/sh -c so users can use shell syntax (pipes, redirects).
	cmd := exec.CommandContext(ctx, "sh", "-c", req.Command)
	if req.Cwd != "" {
		cmd.Dir = req.Cwd
	}
	if len(req.Env) > 0 {
		cmd.Env = req.Env
	}
	out, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}
	body := string(out)
	c.JSON(http.StatusOK, execResponse{
		ExitCode: exitCode,
		Stdout:   body,
		Stderr:   "",
		Result:   body,
	})
}

type codeRunRequest struct {
	Code     string `json:"code"`
	Language string `json:"language,omitempty"` // "python" (default), "bash"
	Timeout  int    `json:"timeout,omitempty"`
}

// CodeRun executes a code snippet (python by default).
func CodeRun(c *gin.Context) {
	var req codeRunRequest
	if err := c.BindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	if req.Code == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "code required"})
		return
	}

	var cmdArgs []string
	switch req.Language {
	case "", "python", "python3":
		cmdArgs = []string{"python3", "-c", req.Code}
	case "bash", "sh":
		cmdArgs = []string{"sh", "-c", req.Code}
	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "unsupported language: " + req.Language})
		return
	}

	ctx := c.Request.Context()
	if req.Timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, time.Duration(req.Timeout)*time.Second)
		defer cancel()
	}

	cmd := exec.CommandContext(ctx, cmdArgs[0], cmdArgs[1:]...)
	out, err := cmd.CombinedOutput()
	exitCode := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		} else {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}
	}
	c.JSON(http.StatusOK, execResponse{
		ExitCode: exitCode,
		Stdout:   string(out),
		Result:   string(out),
	})
}
