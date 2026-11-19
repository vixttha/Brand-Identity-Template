#!/usr/bin/env bash
set -euo pipefail
checker="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/check_checkout.sh"

repo=$(mktemp -d)
trap 'rm -rf -- "$repo"' EXIT
cd "$repo"
git init -q
export GIT_AUTHOR_NAME='Vault fixture' GIT_COMMITTER_NAME='Vault fixture'
export GIT_AUTHOR_EMAIL='vault@example.invalid' GIT_COMMITTER_EMAIL='vault@example.invalid'
tree=$(git mktree </dev/null)
common=$(git -c commit.gpgsign=false commit-tree "$tree" -m common)
base=$(git -c commit.gpgsign=false commit-tree "$tree" -p "$common" -m base)
head=$(git -c commit.gpgsign=false commit-tree "$tree" -p "$common" -m head)
merge=$(git -c commit.gpgsign=false commit-tree "$tree" -p "$base" -p "$head" -m merge)

reject() {
  local expected=$1
  shift
  local output
  if output=$(bash "$checker" "$@" 2>&1); then
    printf 'Checkout checker accepted a negative control: %s\n' "$expected" >&2
    exit 1
  fi
  if [[ "$output" != *"$expected"* ]]; then
    printf 'Unexpected checkout checker error: %s\n' "$output" >&2
    exit 1
  fi
}

git checkout --quiet --detach "$head"
bash "$checker" "$head"
reject 'Checkout mismatch' "$base"
reject 'Merge parents mismatch' "$head" "$base" "$head"
printf 'GIT-001 PASS: real source SHA accepted, stale SHA and head-only PR rejected.\n'

git checkout --quiet --detach "$merge"
bash "$checker" "$merge" "$base" "$head"
reject 'Merge parents mismatch' "$merge" "$head" "$base"
reject 'Merge parents mismatch' "$merge" "$base" "$common"
reject 'Pass either the checkout SHA alone' "$merge" "$base"
printf 'GIT-002 PASS: only the current ordered two-parent merge is accepted.\n'
