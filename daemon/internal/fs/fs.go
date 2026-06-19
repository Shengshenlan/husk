// Package fs implements the daemon's filesystem endpoints.
package fs

import (
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strconv"

	"github.com/gin-gonic/gin"
)

type fileEntry struct {
	Name    string `json:"name"`
	Path    string `json:"path"`
	IsDir   bool   `json:"is_dir"`
	Size    int64  `json:"size"`
	Mode    string `json:"mode"`
	ModTime string `json:"mod_time"`
}

func List(c *gin.Context) {
	path := c.DefaultQuery("path", "/workspace")
	abs, err := filepath.Abs(path)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	entries, err := os.ReadDir(abs)
	if err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	out := make([]fileEntry, 0, len(entries))
	for _, e := range entries {
		info, err := e.Info()
		if err != nil {
			continue
		}
		out = append(out, fileEntry{
			Name:    e.Name(),
			Path:    filepath.Join(abs, e.Name()),
			IsDir:   e.IsDir(),
			Size:    info.Size(),
			Mode:    info.Mode().String(),
			ModTime: info.ModTime().Format("2006-01-02T15:04:05Z07:00"),
		})
	}
	c.JSON(http.StatusOK, out)
}

func Info(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}
	info, err := os.Stat(path)
	if err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, fileEntry{
		Name:    info.Name(),
		Path:    path,
		IsDir:   info.IsDir(),
		Size:    info.Size(),
		Mode:    info.Mode().String(),
		ModTime: info.ModTime().Format("2006-01-02T15:04:05Z07:00"),
	})
}

func Download(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}
	info, err := os.Stat(path)
	if err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	if info.IsDir() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path is a directory; use tar for that"})
		return
	}
	c.FileAttachment(path, info.Name())
}

func Upload(c *gin.Context) {
	path := c.PostForm("path")
	if path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}
	file, err := c.FormFile("file")
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	src, err := file.Open()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer src.Close()
	dst, err := os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0o644)
	if err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	defer dst.Close()
	written, err := io.Copy(dst, src)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"path": path, "bytes": strconv.FormatInt(written, 10)})
}

func MakeFolder(c *gin.Context) {
	var body struct {
		Path string `json:"path"`
		Mode string `json:"mode,omitempty"`
	}
	if err := c.BindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	mode := os.FileMode(0o755)
	if body.Mode != "" {
		if parsed, err := strconv.ParseUint(body.Mode, 8, 32); err == nil {
			mode = os.FileMode(parsed)
		}
	}
	if err := os.MkdirAll(body.Path, mode); err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"path": body.Path})
}

func Delete(c *gin.Context) {
	path := c.Query("path")
	if path == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "path required"})
		return
	}
	recursive := c.Query("recursive") == "true"
	var err error
	if recursive {
		err = os.RemoveAll(path)
	} else {
		err = os.Remove(path)
	}
	if err != nil {
		c.JSON(httpStatusFor(err), gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, gin.H{"path": path, "deleted": true})
}

func httpStatusFor(err error) int {
	switch {
	case errors.Is(err, os.ErrNotExist):
		return http.StatusNotFound
	case errors.Is(err, os.ErrPermission):
		return http.StatusForbidden
	default:
		return http.StatusInternalServerError
	}
}
