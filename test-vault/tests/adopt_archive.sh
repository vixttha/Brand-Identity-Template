#!/usr/bin/env bash
# Download the public archives and use them in an existing Git project.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

source_repo=$(git rev-parse --show-toplevel)
workspace=$(mktemp -d)
trap 'rm -rf -- "$workspace"' EXIT
cd "$source_repo"

repository=https://github.com/vixttha/Brand-Identity-Template
tag=v0.0.2
release_sha=87d0f9aedbe69ca4b16815d6b3329efcf5889da9
main_ref=refs/heads/main
release_ref=refs/tags/$tag

download() {
  curl --fail --silent --show-error --location --retry 2 --max-time 30 "$1" -o "$2"
  unzip -tq "$2"
}

extract() {
  unzip -q "$1" -d "$2"
  local trees=("$2"/*)
  [[ "${#trees[@]}" == 1 && -d "${trees[0]}/brand-identity" && -f "${trees[0]}/README.md" ]]
  result=${trees[0]}
}

compare_checkout() {
  mkdir "$workspace/expected"
  git -C "$source_repo" archive "$1" brand-identity | tar -x -C "$workspace/expected"
  diff -r -- "$workspace/expected/brand-identity" "$2/brand-identity"
  rm -r -- "$workspace/expected"
}

# Test the URL readers actually use, and avoid comparing snapshots captured on
# opposite sides of a concurrent update of main.
main_url=$(sed -n 's/.*\[Brand Identity Template ZIP\](\([^)]*\)).*/\1/p' README.md)
[[ "$main_url" == "$repository/archive/refs/heads/main.zip" ]]
matching_main=
for attempt in 1 2 3; do
  git fetch -q --no-tags "$repository.git" "$main_ref"
  before=$(git rev-parse FETCH_HEAD)
  download "$main_url" "$workspace/main.zip"
  git fetch -q --no-tags "$repository.git" "$main_ref"
  after=$(git rev-parse FETCH_HEAD)
  if [[ "$before" == "$after" ]]; then
    matching_main=$before
    break
  fi
done
[[ -n "$matching_main" ]]
extract "$workspace/main.zip" "$workspace/main"
compare_checkout "$matching_main" "$result"
printf 'ZIP-001 PASS: README download contains the complete kit at main %s.\n' "$matching_main"

git fetch -q --no-tags "$repository.git" "$release_ref"
[[ "$(git rev-parse 'FETCH_HEAD^{commit}')" == "$release_sha" ]]
download "$repository/archive/refs/tags/$tag.zip" "$workspace/release.zip"
extract "$workspace/release.zip" "$workspace/release"
compare_checkout "$release_sha" "$result"
release_tree=$result
printf 'ZIP-002 PASS: tagged ZIP matches the release kit and license at %s.\n' "$release_sha"

consumer="$workspace/Existing product with spaces"
mkdir -p "$consumer/docs"
git -C "$consumer" init -q
printf '# Existing instructions\n' > "$consumer/AGENTS.md"
printf '# Existing README\n' > "$consumer/README.md"
printf '# Existing product evidence\n' > "$consumer/docs/evidence.md"
git -C "$consumer" add .
git -C "$consumer" -c user.name='Vault fixture' -c user.email='vault@example.invalid' \
  -c commit.gpgsign=false commit -qm 'Existing project'
original_head=$(git -C "$consumer" rev-parse HEAD)

cd "$consumer"
cp -R "$release_tree/brand-identity" .
python3 brand-identity/verify.py
python3 - <<'PY'
import json
from pathlib import Path

manifest = Path("brand-identity/09-assets/manifest.json")
data = json.loads(manifest.read_text(encoding="utf-8"))
assert data["kind"] == "template" and data["assets"] == []
data["kind"] = "project"
manifest.write_text(json.dumps(data) + "\n", encoding="utf-8")
PY
python3 brand-identity/verify.py
printf 'ZIP-003 PASS: documented adoption works from an existing project path with spaces.\n'
cmp -- "$release_tree/brand-identity/LICENSE" brand-identity/LICENSE
[[ "$(git rev-parse HEAD)" == "$original_head" ]]
[[ "$(git status --porcelain --untracked-files=normal)" == '?? brand-identity/' ]]
printf 'ZIP-004 PASS: original host files, Git history and copied license are preserved.\n'
