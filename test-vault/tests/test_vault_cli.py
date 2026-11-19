"""Exercise the vendored Lydite catalog and execution-receipt CLI contracts."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from png_fixtures import write_json

VAULT = Path(__file__).resolve().parents[1]
HEADER = (
    "| Case | Area | Priority | Suggested implementation | Expected outcome |\n"
    "| --- | --- | --- | --- | --- |\n"
)
ROW = "| PNG-001 | PNG | P0 | Python | PASS |\n"


class VaultCLI(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.vault = VAULT
        self.catalog = self.root / "cases.md"
        self.catalog.write_text(HEADER + ROW, encoding="utf-8")

    def run_cli(self, script, *arguments):
        env = os.environ.copy()
        env.pop("GITHUB_STEP_SUMMARY", None)
        return subprocess.run(
            [sys.executable, "-B", str(self.vault / script), *arguments],
            cwd=self.root, env=env, capture_output=True, text=True, encoding="utf-8",
            timeout=15,
        )


class CatalogTests(VaultCLI):
    def validate(self, *args):
        return self.run_cli("validate_catalog.py", "--catalog", str(self.catalog), *args)

    def test_escaped_pipes_and_fenced_examples_do_not_change_case_count(self):
        row = ROW.replace("Python", r"Python \| CLI")
        self.catalog.write_text("```markdown\n" + HEADER + ROW + "```\n\n" + HEADER + row,
                                encoding="utf-8")
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 unique cases across 1 topics", result.stdout)

    def test_catalog_ignores_comments_code_and_unrelated_tables(self):
        commented = "<!-- optional example\n" + HEADER + ROW + "-->\n\n"
        indented = "".join(f"    {line}\n" for line in (HEADER + ROW).splitlines())
        unrelated = "| Language | Runner |\n| --- | --- |\n| Python | Ubuntu |\n\n"
        catalog = "\n".join(line.strip("| ") for line in (HEADER + ROW).splitlines())
        self.catalog.write_text(commented + indented + "\n" + unrelated + catalog + "\n",
                                encoding="utf-8")
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 unique cases across 1 topics", result.stdout)

    def test_bad_catalog_structure_fails(self):
        for catalog, reason in (
            (HEADER, "no cases found"),
            (HEADER.splitlines()[0] + "\n" + ROW, "table divider"),
            (HEADER + ROW + ROW, "duplicate case PNG-001"),
            (HEADER + ROW.replace("P0", "P9"), "invalid case row"),
            (HEADER + ROW.replace("PNG-001", "PNG-1"), "invalid case row"),
        ):
            with self.subTest(reason=reason):
                self.catalog.write_text(catalog, encoding="utf-8")
                result = self.validate()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(reason, result.stderr)

    def test_topic_registry_must_match_the_catalog(self):
        topics = self.root / "topics.json"
        write_json(topics, ["PNG"])
        result = self.validate("--topics", str(topics))
        self.assertEqual(result.returncode, 0, result.stderr)
        for values, reason in (
            (["PNG", "PNG"], "duplicate topic ID"),
            (["OTHER"], "missing topics: OTHER; unknown topics: PNG"),
            ([], "nonempty JSON array"),
        ):
            with self.subTest(values=values):
                write_json(topics, values)
                result = self.validate("--topics", str(topics))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(reason, result.stderr)


class ReceiptTests(VaultCLI):
    def setUp(self):
        super().setUp()
        self.vault = self.root / "test-vault"
        self.vault.mkdir()
        for name in ("verify_receipts.py", "validate_catalog.py", "source_commit.py"):
            shutil.copyfile(VAULT / name, self.vault / name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "test-vault", "cases.md"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Vault Test", "-c", "user.email=vault@example.invalid",
             "-c", "commit.gpgsign=false", "commit", "-qm", "Fixture input"],
            cwd=self.root, check=True,
        )
        self.checkout = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root,
                                               text=True).strip()
        self.case_path = self.root / "case.json"
        self.case = {"schema_version": 1, "case_id": "PNG-001",
                     "required_checks": ["python", "browser"], "shared_evidence": True}
        write_json(self.case_path, self.case)
        self.receipts = self.root / "receipts"
        self.receipts.mkdir()
        self.evidence = self.root / "evidence.txt"
        self.evidence.write_bytes(b"Shared input\n")
        self.receipt = {
            "schema_version": 1, "case_id": "PNG-001", "checkout_sha": self.checkout,
            "run_id": "1234", "attempt": "2", "status": "pass",
            "environment": {"os": "Fixture OS", "runtime": "Fixture runtime"},
            "evidence_sha256": hashlib.sha256(b"Shared input\n").hexdigest(),
        }
        self.write_receipt("python")
        self.write_receipt("browser")

    def write_receipt(self, check, *, filename=None, **fields):
        write_json(self.receipts / (filename or f"{check}.json"),
                   {**self.receipt, "check_id": check, **fields})

    def verify(self, *, use_evidence=True, attempt="2", catalog=None):
        args = [
            "--case", str(self.case_path),
            "--catalog", str(catalog or self.catalog),
            "--receipts", str(self.receipts),
            "--run-id", "1234",
            "--attempt", attempt,
        ]
        if use_evidence:
            args.extend(("--evidence", str(self.evidence)))
        return self.run_cli("verify_receipts.py", *args)

    def assert_verdict(self, result, outcome, *details):
        self.assertEqual(result.returncode, 0 if outcome == "PASS" else 1,
                         result.stdout + result.stderr)
        self.assertIn(f"**Overall: {outcome}**", result.stdout)
        for detail in details:
            self.assertIn(detail, result.stdout)

    def test_shared_observation_passes_with_both_independent_receipts(self):
        self.assert_verdict(self.verify(), "PASS", f"Checkout: {self.checkout}",
                            "| python | PASS |", "| browser | PASS |", "Attempt: 2",
                            "Legacy receipt v1")

    def test_v2_receipts_bind_exact_plan_bytes(self):
        self.case["schema_version"] = 2
        write_json(self.case_path, self.case)
        plan = self.case_path.read_bytes()
        original = hashlib.sha256(plan).hexdigest()
        for check in self.case["required_checks"]:
            self.write_receipt(check, schema_version=2, case_plan_sha256=original)
        self.assert_verdict(self.verify(), "PASS", f"Case plan SHA-256: {original}")
        self.case_path.write_bytes(plan + b"\n")
        self.assert_verdict(self.verify(), "FAIL", "| python | INVALID |", "| browser | INVALID |",
                            "case_plan_sha256 does not match")
        self.case_path.write_bytes(plan)
        self.write_receipt("browser")
        self.assert_verdict(self.verify(), "FAIL", "| browser | INVALID |")

    def test_receipts_require_a_clean_checkout_and_tracked_catalog(self):
        untracked = self.root / "untracked.md"
        shutil.copyfile(self.catalog, untracked)
        self.assert_verdict(self.verify(catalog=untracked), "FAIL", "source must be tracked")
        self.catalog.write_text(HEADER + ROW + "\nEdited tracked catalog\n", encoding="utf-8")
        self.assert_verdict(self.verify(), "FAIL", "commit tracked changes")

    def test_post_run_edit_of_shared_evidence_fails_both_receipts(self):
        self.evidence.write_bytes(b"Changed input\n")
        self.assert_verdict(self.verify(), "FAIL", "| python | INVALID |", "| browser | INVALID |",
                            "evidence_sha256 does not match")

    def test_missing_duplicate_and_undeclared_receipts_are_rejected(self):
        (self.receipts / "browser.json").unlink()
        self.assert_verdict(self.verify(), "FAIL", "| browser | MISSING |")
        self.write_receipt("browser")
        self.write_receipt("browser", filename="duplicate.json")
        self.assert_verdict(self.verify(), "FAIL", "| browser | DUPLICATE |")
        (self.receipts / "duplicate.json").unlink()
        self.write_receipt("unknown")
        self.assert_verdict(self.verify(), "FAIL", "undeclared check receipt")

    def test_stale_or_cross_case_receipts_do_not_count(self):
        for field, alternate in (
            ("attempt", "1"), ("run_id", "1233"),
            ("checkout_sha", "0" * 40), ("case_id", "PNG-002"),
        ):
            with self.subTest(field=field):
                self.write_receipt("browser", **{field: alternate})
                self.assert_verdict(self.verify(), "FAIL", "| browser | INVALID |",
                                    f"{field} does not match")

    def test_fail_skip_and_blocked_are_distinct_nonpassing_verdicts(self):
        for status in ("fail", "skip", "blocked"):
            with self.subTest(status=status):
                self.write_receipt("browser", status=status)
                self.assert_verdict(self.verify(), "FAIL", f"| browser | {status.upper()} |")

    def test_invalid_receipt_schema_cannot_claim_pass(self):
        for fields, reason in (
            ({"schema_version": True}, "unsupported schema version"),
            ({"extra": "ignored?"}, "missing or unknown fields"),
            ({"environment": {"os": "", "runtime": "node"}}, "nonempty os and runtime strings"),
            ({"status": "green"}, "unrecognized outcome"),
        ):
            with self.subTest(fields=fields):
                self.write_receipt("browser", **fields)
                self.assert_verdict(self.verify(), "FAIL", "| browser | INVALID |", reason)

    def test_duplicate_json_keys_do_not_override_a_receipt(self):
        browser = self.receipts / "browser.json"
        raw = json.dumps({**self.receipt, "check_id": "browser", "status": "fail"})
        browser.write_text(raw[:-1] + ', "status": "pass"}', encoding="utf-8")
        self.assert_verdict(self.verify(), "FAIL", "unreadable or invalid receipt")

    def test_case_without_shared_evidence_requires_null_digest(self):
        self.case["shared_evidence"] = False
        write_json(self.case_path, self.case)
        self.write_receipt("python", evidence_sha256=None)
        self.write_receipt("browser", evidence_sha256=None)
        self.assert_verdict(self.verify(use_evidence=False), "PASS")
        self.assert_verdict(self.verify(), "FAIL", "evidence argument must match")
        self.write_receipt("browser")
        self.assert_verdict(self.verify(use_evidence=False), "FAIL", "evidence_sha256 does not match")

    def test_case_and_attempt_must_be_declared_and_valid(self):
        self.assert_verdict(self.verify(attempt="02"), "FAIL", "positive decimal strings")
        self.case["case_id"] = "PNG-002"
        write_json(self.case_path, self.case)
        self.assert_verdict(self.verify(), "FAIL", "case ID must be registered")
        self.case["case_id"] = "PNG-001"
        self.case["required_checks"] = ["browser", "browser"]
        write_json(self.case_path, self.case)
        self.assert_verdict(self.verify(), "FAIL", "nonempty list of unique check IDs")
