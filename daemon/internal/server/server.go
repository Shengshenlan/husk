// Package server wires the daemon's HTTP routes.
package server

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/husklabs/husk-daemon/internal/fs"
	"github.com/husklabs/husk-daemon/internal/proc"
)

// New returns a fully-configured *gin.Engine for the daemon.
func New(version string) http.Handler {
	gin.SetMode(gin.ReleaseMode)
	r := gin.New()
	r.Use(gin.Recovery())

	// ── meta ──
	r.GET("/version", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"version": version, "name": "husk-daemon"})
	})
	r.GET("/work-dir", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"path": "/workspace"}) })
	r.GET("/project-dir", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"path": "/workspace"}) })
	r.GET("/user-home-dir", func(c *gin.Context) { c.JSON(http.StatusOK, gin.H{"path": "/root"}) })

	// ── files ──
	files := r.Group("/files")
	{
		files.GET("", fs.List)
		files.GET("/", fs.List)
		files.GET("/info", fs.Info)
		files.GET("/download", fs.Download)
		files.POST("/upload", fs.Upload)
		files.POST("/folder", fs.MakeFolder)
		files.DELETE("", fs.Delete)
		files.DELETE("/", fs.Delete)
	}

	// ── process ──
	process := r.Group("/process")
	{
		process.POST("/execute", proc.Execute)
		process.POST("/code-run", proc.CodeRun)
	}

	return r
}
