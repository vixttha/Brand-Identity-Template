#!/usr/bin/env bash
# Produce one fixture inventory for the actual verifier and Chromium.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
export PYTHONDONTWRITEBYTECODE=1

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

record_receipt() {
  python3 - "$receipt_dir/$1.json" "$1" "$2" "$3" "$manifest" "$run_id" "$attempt" <<'PY'
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

out, check, runtime, status, manifest, run_id, attempt = sys.argv[1:]
checkout = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
receipt = {
    "schema_version": 1,
    "case_id": "PNG-010",
    "check_id": check,
    "checkout_sha": checkout,
    "run_id": run_id,
    "attempt": attempt,
    "environment": {"os": platform.platform(), "runtime": runtime},
    "status": status,
    "evidence_sha256": hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
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

if npm --prefix test-vault/browser test; then
  browser_status=pass
else
  browser_status=fail
fi
record_receipt chromium "Node.js $(node --version)" "$browser_status"

python3 test-vault/verify_receipts.py --case test-vault/tests/png-browser-case.json \
  --receipts "$receipt_dir" --evidence "$manifest" --run-id "$run_id" --attempt "$attempt"
