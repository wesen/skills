//go:build !embed

package web

import (
	"io/fs"
	"os"
	"path/filepath"
)

// PublicFS is nil unless we detect a local generated build output on disk.
// This makes `go run` usable after `go generate` has populated embed/public.
var PublicFS fs.FS = diskPublicFS()

func diskPublicFS() fs.FS {
	repoRoot, err := findRepoRootFromCWD()
	if err != nil {
		return nil
	}

	publicDir := filepath.Join(repoRoot, "internal", "web", "embed", "public")
	if _, err := os.Stat(filepath.Join(publicDir, "index.html")); err != nil {
		return nil
	}

	return os.DirFS(publicDir)
}

func findRepoRootFromCWD() (string, error) {
	dir, err := os.Getwd()
	if err != nil {
		return "", err
	}

	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", os.ErrNotExist
		}
		dir = parent
	}
}
