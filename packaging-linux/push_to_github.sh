#!/bin/bash
set -euo pipefail

# Usage: ./push_to_github.sh "Commit message" [branch]
# Environment overrides:
#   GIT_REMOTE_URL - remote repository URL (default: https://github.com/steve-rock-wheelhouser/image-inpainter.git)
#   REMOTE_NAME    - remote name to use (default: origin)
# Example:
#   GIT_REMOTE_URL="git@github.com:steve-rock-wheelhouser/image-inpainter.git" ./push_to_github.sh "Initial commit" main

if [ $# -lt 1 ]; then
    echo "Error: Please provide a commit message."
    echo "Usage: ./push_to_github.sh \"Your commit message\" [branch]"
    exit 1
fi

COMMIT_MSG="$1"
# Determine branch: use provided, else try to get current branch, fallback to 'main'
BRANCH_RAW="${2:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)}"
# Sanitize branch: take first line and remove CR/LF characters to avoid invalid refspecs
BRANCH="$(printf '%s' "$BRANCH_RAW" | sed -n '1p' | tr -d '\r' | tr -d '\n')"
REMOTE_NAME="${REMOTE_NAME:-origin}"
REMOTE_URL="${GIT_REMOTE_URL:-https://github.com/steve-rock-wheelhouser/image-inpainter.git}"

init_repo_if_needed() {
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        echo "--- Git repository not found. Initializing... ---"
        git init
        # Ensure main branch exists locally
        git checkout -b "$BRANCH" || true
    fi
}

init_repo_if_needed

echo "--- Staging files ---"
git add .

echo "--- Commit ---"
# If no commits exist yet, create the initial commit even if no files are staged
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    git commit -m "$COMMIT_MSG" || {
        # If commit failed (e.g., no files), create an empty initial commit
        git commit --allow-empty -m "$COMMIT_MSG"
    }
else
    if git diff --cached --quiet; then
        echo "No changes staged for commit. Skipping commit."
    else
        git commit -m "$COMMIT_MSG"
    fi
fi

echo "--- Ensuring remote '$REMOTE_NAME' is configured ---"
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
    CURRENT_URL=$(git remote get-url "$REMOTE_NAME")
    if [ "$CURRENT_URL" != "$REMOTE_URL" ]; then
        echo "Warning: remote '$REMOTE_NAME' points to: $CURRENT_URL"
        echo "If you want to change it to: $REMOTE_URL run:" 
        echo "  git remote set-url $REMOTE_NAME $REMOTE_URL"
    fi
else
    echo "Adding remote '$REMOTE_NAME' -> $REMOTE_URL"
    git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

echo "--- Pushing to $REMOTE_NAME/$BRANCH ---"
# Use -u on first push to set upstream. Check remote branch existence via git ls-remote.
if git ls-remote --exit-code --heads "$REMOTE_NAME" "$BRANCH" >/dev/null 2>&1; then
    git push "$REMOTE_NAME" "$BRANCH"
else
    git push -u "$REMOTE_NAME" "$BRANCH"
fi

echo "Done."
