#!/usr/bin/env bash
# Exercise the offline candidate ZIP check against disposable commits.
set -euo pipefail

script="$(git rev-parse --show-toplevel)/test-vault/tests/adopt_archive.sh"
workspace=$(mktemp -d)
trap 'rm -rf -- "$workspace"' EXIT
repo="$workspace/Candidate fixture"
mkdir "$repo"
git archive HEAD README.md brand-identity | tar -x -C "$repo"
cd "$repo"
git init -q

commit() {
  git add -A
  git -c user.name='Vault fixture' -c user.email='vault@example.invalid' \
    -c commit.gpgsign=false commit -qm "$1"
}

reject() {
  local reason=$1 output
  if output=$(bash "$script" --candidate-only 2>&1); then
    printf 'Broken candidate passed ZIP adoption:\n%s\n' "$output" >&2
    return 1
  fi
  if [[ "$output" != *"$reason"* ]]; then
    printf 'Candidate failed for an unexpected reason:\n%s\n' "$output" >&2
    return 1
  fi
}

commit 'Valid candidate'
valid=$(git rev-parse HEAD)
rm brand-identity/LICENSE
output=$(bash "$script" --candidate-only)
[[ "$output" == *"ZIP-005 PASS: candidate $valid"* ]]
printf 'ZIP-006 PASS: ZIP uses the committed tree even with different working files.\n'

commit 'Remove required license'
reject 'Missing regular brand identity LICENSE'
printf 'ZIP-007 PASS: ZIP adoption rejects a candidate commit missing its license.\n'

git restore --source="$valid" -- brand-identity
printf 'brand-identity/09-assets/manifest.json export-ignore\n' > .gitattributes
commit 'Exclude the asset manifest from exported archives'
reject 'manifest.json'
printf 'ZIP-008 PASS: ZIP adoption rejects a tracked manifest excluded from the artifact.\n'
