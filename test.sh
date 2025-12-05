#!/usr/bin/env bash

# This script verifies all commits in the current branch for valid signatures.
# Usage: ./verify_commits.sh [<branch>]
# If no branch given, uses HEAD (current branch).

set -euo pipefail

branch=${1:-HEAD}

# Get all commit hashes in this branch (excluding merge commits if you want)
commits=$(git rev-list "${branch}")

if [ -z "$commits" ]; then
  echo "No commits found on branch ${branch}"
  exit 1
fi

echo "Verifying ${#commits[@]} commits on branch '${branch}'..."

# Counters
total=0
valid=0
invalid=0
unsigned=0

# Iterate commits
for commit in $commits; do
  total=$((total + 1))
  # Try verifying signature
  # git verify-commit returns non-zero if signature invalid or missing
  if git verify-commit --verbose "$commit" >/dev/null 2>&1; then
    echo "✔ $commit: valid"
    valid=$((valid + 1))
  else
    # Check if it's unsigned vs invalid
    # Using --show-signature to inspect
    sig_output=$(git show --show-signature -s "$commit" 2>&1 || true)
    if echo "$sig_output" | grep -q "No signature"; then
      echo "✘ $commit: unsigned"
      unsigned=$((unsigned + 1))
    else
      echo "✘ $commit: invalid signature"
      invalid=$((invalid + 1))
    fi
  fi
done

# Summary
echo "---------------------------"
echo "Total commits checked: $total"
echo "Valid signatures     : $valid"
echo "Invalid signatures   : $invalid"
echo "Unsigned commits     : $unsigned"

# Exit non-zero if any invalid or unsigned
if [ "$invalid" -gt 0 ] || [ "$unsigned" -gt 0 ]; then
  exit 1
else
  exit 0
fi

