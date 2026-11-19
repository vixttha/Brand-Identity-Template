#!/usr/bin/env bash
# Verify the actual checked-out commit and, for PRs, the ordered merge parents.
set -euo pipefail

expected_sha=${1:?expected checkout SHA required}
actual_sha=$(git rev-parse HEAD)
if [[ "$actual_sha" != "$expected_sha" ]]; then
  printf 'Checkout mismatch: expected %s, got %s\n' "$expected_sha" "$actual_sha" >&2
  exit 1
fi

if [[ $# == 1 ]]; then
  printf 'Source checkout: %s\n' "$actual_sha"
elif [[ $# == 3 ]]; then
  mapfile -t parents < <(git cat-file -p HEAD | sed -n '/^$/q; s/^parent //p')
  if [[ "${#parents[@]}" != 2 || "${parents[0]}" != "$2" || "${parents[1]}" != "$3" ]]; then
    printf 'Merge parents mismatch: expected base %s and head %s\n' "$2" "$3" >&2
    exit 1
  fi
  printf 'PR merge checkout: %s\n\n- Base: %s\n- Head: %s\n' "$actual_sha" "$2" "$3"
else
  printf 'Pass either the checkout SHA alone or the checkout, base and head SHAs\n' >&2
  exit 2
fi
