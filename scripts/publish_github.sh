#!/usr/bin/env sh
# Publish the existing five-commit repository to the authenticated GitHub user.
# Requires GitHub CLI (gh) and prior `gh auth login`.
set -eu
cd "$(dirname "$0")/.."
if ! command -v gh >/dev/null 2>&1; then
    echo "GitHub CLI (gh) not found. Install gh and run: gh auth login" >&2
    exit 1
fi
if ! gh auth status >/dev/null 2>&1; then
    echo "Not authenticated. Run: gh auth login" >&2
    exit 1
fi
if git remote get-url origin >/dev/null 2>&1; then
    echo "Remote origin is already configured; push with: git push -u origin main"
    exit 1
fi
# This creates a NEW repository; it does not touch the practical-work-1 repo.
gh repo create configuration-pr2-21 --public --source=. --remote=origin --push
