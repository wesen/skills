---
name: git-commit-instructions
description: "Practical Git hygiene for staging and committing: review diffs, stage intentionally, avoid committing noise/build artifacts/secrets, and recover from accidental staging or committing. Use when a user asks how to commit changes, write a commit workflow checklist, unstage/remove accidental files, or verify `.gitignore` behavior."
---

# Git Commit Instructions

## Overview

Use this checklist to keep commits focused, reviewable, and free of build artifacts and other noise.

## Before Every Commit

```bash
git status --porcelain
git diff --stat          # unstaged changes
git diff --cached --stat # staged changes
```

## Stage Intentionally (preferred)

```bash
git add path/to/file.go path/to/dir/
```

Use `git add -A` only when you are sure you want every change.

## Inspect What Will Be Committed

```bash
git diff --cached --name-only
```

## Commit Pattern

```bash
git commit -m "Short summary of change"
git rev-parse HEAD
```

## Never Commit (common noise)

Avoid committing:
- `node_modules/`, `vendor/`
- `dist/`, `build/`, `out/`
- `.env`, `.env.local`
- binaries (`*.exe`, `*.bin`, etc.)
- logs (`*.log`)
- OS/IDE junk (`.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/` unless shared)
- test artifacts (`coverage/`, `*.cover`)
- temp dirs (`tmp/`, `temp/`)

## Quick Checks

```bash
git status --ignored
git check-ignore -v path/to/file
```

## If You Accidentally Staged Something

```bash
git reset HEAD path/to/file   # unstage one file
git reset HEAD                # unstage everything
```

## If Noise Got Committed

```bash
git rm --cached path/to/noise
echo "path/to/noise" >> .gitignore
git add .gitignore
git commit --amend --no-edit  # if it was the last commit
```

## Reference

Load `references/git-commit-instructions.md` for the full command list and recovery patterns.
