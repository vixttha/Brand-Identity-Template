#!/usr/bin/env bash
# Produce one fixture inventory for the actual verifier and Chromium.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export PYTHONDONTWRITEBYTECODE=1

plan=test-vault/tests/png-browser-case.json
browser=test-vault/browser
required="$browser/required-tests.json"
verify_results="$browser/verify-results.cjs"
checkout=$(python3 test-vault/source_commit.py "$plan" test-vault/cases.md \
  test-vault/tests/browser.sh test-vault/tests/png_fixtures.py \
  brand-identity/verify.py "$browser/png.spec.cjs" "$required" "$verify_results")

workspace=$(mktemp -d)
trap 'rm -rf -- "$workspace"' EXIT
mkdir -p "$workspace/project"
kit="$workspace/project/brand-identity"
cp -R brand-identity "$kit"

python3 test-vault/tests/png_fixtures.py "$kit"
python3 - "$kit" <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, "brand-identity")
from test_verify import scored_decision
sys.path.insert(0, "test-vault/tests")
from png_fixtures import write_json

write_json(Path(sys.argv[1]) / "01-strategy/creative-decision.json", scored_decision())
PY

manifest="$kit/09-assets/manifest.json"
export BRAND_BROWSER_ASSETS="$kit/09-assets"
receipt_dir="$workspace/receipts"
mkdir "$receipt_dir"
run_id=${GITHUB_RUN_ID:-1}
attempt=${GITHUB_RUN_ATTEMPT:-1}
bindings=$(python3 - "$plan" "$manifest" <<'PYTHON'
import hashlib
import json
from pathlib import Path
import sys

plan = Path(sys.argv[1]).read_bytes()
manifest = Path(sys.argv[2]).read_bytes()
print(json.loads(plan)["case_id"], hashlib.sha256(plan).hexdigest(),
      hashlib.sha256(manifest).hexdigest())
PYTHON
)
read -r case_id case_plan_sha256 evidence_sha256 <<< "$bindings"

record_receipt() {
  python3 - "$receipt_dir/$1.json" "$1" "$2" "$3" "$checkout" "$run_id" "$attempt" \
    "$case_id" "$case_plan_sha256" "$evidence_sha256" <<'PY'
import json
from pathlib import Path
import platform
import sys

(out, check, runtime, status, checkout, run_id, attempt,
 case_id, case_plan_sha256, evidence_sha256) = sys.argv[1:]
receipt = {
    "schema_version": 2,
    "case_id": case_id,
    "check_id": check,
    "checkout_sha": checkout,
    "run_id": run_id,
    "attempt": attempt,
    "environment": {"os": platform.platform(), "runtime": runtime},
    "status": status,
    "case_plan_sha256": case_plan_sha256,
    "evidence_sha256": evidence_sha256,
}
Path(out).write_text(json.dumps(receipt) + "\n", encoding="utf-8")
PY
}

if (cd "$workspace/project" && python3 brand-identity/verify.py --ready-for-handoff); then
  python_status=pass
else
  python_status=fail
fi
record_receipt python-verifier "$(python3 --version)" "$python_status"

report="$workspace/playwright.json"
if PLAYWRIGHT_JSON_OUTPUT_FILE="$report" npm --prefix "$browser" test -- --reporter=list,json &&
   node "$verify_results" "$required" "$report"; then
  browser_status=pass
else
  browser_status=fail
fi
record_receipt chromium "Node.js $(node --version)" "$browser_status"

if [[ -n "${LYDITE_BROWSER_EVIDENCE_DIR:-}" ]]; then
  bundle="$LYDITE_BROWSER_EVIDENCE_DIR"
  mkdir -p "$bundle/receipts"
  cp "$plan" "$bundle/case.json"
  cp "$manifest" "$bundle/manifest.json"
  cp "$receipt_dir/python-verifier.json" "$receipt_dir/chromium.json" "$bundle/receipts/"
  plan="$bundle/case.json"
  manifest="$bundle/manifest.json"
  receipt_dir="$bundle/receipts"
fi

python3 test-vault/verify_receipts.py --case "$plan" \
  --receipts "$receipt_dir" --evidence "$manifest" --run-id "$run_id" --attempt "$attempt"
