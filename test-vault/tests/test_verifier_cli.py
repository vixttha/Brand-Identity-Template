"""Run the adopted command against independently constructed inputs."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from png_fixtures import asset_record, rgba_pattern, write_json

REPOSITORY = Path(__file__).resolve().parents[2]
KIT = REPOSITORY / "brand-identity"
sys.path.insert(0, str(KIT))
from test_verify import scored_decision


class AdoptedKit(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "Adopted project"
        self.root.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.kit = self.root / KIT.name
        shutil.copytree(KIT, self.kit, ignore=shutil.ignore_patterns("__pycache__"))
        self.asset_dir = self.kit / "09-assets"
        self.manifest_path = self.asset_dir / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.manifest["kind"] = "project"
        self.save_manifest()
        self.decision_path = self.kit / "01-strategy" / "creative-decision.json"
        self.brief = self.kit / "01-strategy" / "brief.md"

    def save_manifest(self):
        write_json(self.manifest_path, self.manifest)

    def add_assets(self, *roles, status="approved"):
        write_json(self.decision_path, scored_decision())
        for role in roles:
            filename = f"{role}.png"
            payload = rgba_pattern()
            (self.asset_dir / filename).write_bytes(payload)
            self.manifest["assets"].append(asset_record(filename, payload, role=role, status=status))
        self.save_manifest()

    def add_link(self, target):
        with self.brief.open("a", encoding="utf-8") as file:
            file.write(f"\n[Fixture evidence]({target})\n")

    def run_verifier(self, *args):
        return subprocess.run(
            [sys.executable, "-B", "brand-identity/verify.py", *args],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8",
            timeout=15,
        )

    def assert_accepted(self, result, text="Verified project kit"):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(text, result.stdout)

    def assert_rejected(self, result, reason):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(reason, result.stderr)
        self.assertNotIn("Verified project kit", result.stdout)


class VerifierCLITests(AdoptedKit):
    def test_invalid_manifest_version_or_kind_is_rejected(self):
        for key, value, reason in (
            ("kit_version", "v999", "Unexpected kit version"),
            ("kind", "unknown", "Invalid kit kind"),
        ):
            with self.subTest(key=key):
                write_json(self.manifest_path, {**self.manifest, key: value})
                self.assert_rejected(self.run_verifier(), reason)

    def test_unconfirmed_empty_project_can_be_work_in_progress(self):
        self.assert_accepted(self.run_verifier())
        self.assert_rejected(self.run_verifier("--ready-for-artwork"), "initial logo category")

    def test_template_cannot_advance_to_artwork(self):
        self.manifest["kind"] = "template"
        self.save_manifest()
        write_json(self.decision_path, scored_decision())
        self.assert_rejected(self.run_verifier("--ready-for-artwork"), "Start a project kit")

    def test_registered_export_cannot_bypass_stale_name_confirmation(self):
        self.add_assets("logo")
        decision = scored_decision()
        decision["names"]["wordmark"] = "Example"
        write_json(self.decision_path, decision)
        self.assert_rejected(self.run_verifier(), "Confirm the exact wordmark")

    def test_weights_beat_unweighted_tie_and_tied_leaders_are_allowed(self):
        decision = scored_decision()
        scores = decision["concepts"]
        scores[0]["scores"] = dict(brand_fit=5, artistic_character=3, distinctiveness=3, versatility=1)
        scores[1]["scores"] = dict(brand_fit=1, artistic_character=3, distinctiveness=3, versatility=5)
        scores[2]["scores"] = dict(scores[0]["scores"])
        for selected in ("concept-0", "concept-2"):
            decision["selected_concept"] = selected
            write_json(self.decision_path, decision)
            self.assert_accepted(self.run_verifier("--ready-for-artwork"), "name confirmation recorded")
        decision["selected_concept"] = "concept-1"
        write_json(self.decision_path, decision)
        self.assert_rejected(self.run_verifier("--ready-for-artwork"), "highest-scoring")

    def test_invalid_shortlist_and_confirmation_fields_are_rejected(self):
        for field, value, reason in (
            ("id", "concept-1", "Duplicate concept ID"),
            ("category", "emblem", "category must fit the brief"),
            ("rationale", " ", "rationale"),
            ("scores", dict(brand_fit=6, artistic_character=4, distinctiveness=4, versatility=4),
             "integer from 1 through 5"),
        ):
            with self.subTest(field=field):
                decision = scored_decision()
                decision["concepts"][0][field] = value
                write_json(self.decision_path, decision)
                self.assert_rejected(self.run_verifier("--ready-for-artwork"), reason)
        decision = scored_decision()
        decision["confirmation"]["reference"] = " "
        write_json(self.decision_path, decision)
        self.assert_rejected(self.run_verifier("--ready-for-artwork"), "owner confirmation reference")

    def test_handoff_with_approved_roles(self):
        self.add_assets("logo", "wordmark")
        self.assert_accepted(self.run_verifier("--ready-for-handoff"), "2 PNGs")

    def test_handoff_rejects_missing_either_role(self):
        for role in ("logo", "wordmark"):
            with self.subTest(role=role):
                self.add_assets(role)
                self.assert_rejected(self.run_verifier("--ready-for-handoff"), "both logo and wordmark")
                (self.asset_dir / f"{role}.png").unlink()
                self.manifest["assets"].clear()

    def test_draft_and_test_exports_are_permitted_in_inventory(self):
        self.add_assets("logo", "wordmark", status="draft")
        self.assert_accepted(self.run_verifier())
        for asset in self.manifest["assets"]:
            asset["status"] = "test"
        self.save_manifest()
        self.assert_accepted(self.run_verifier())

    def test_duplicate_or_missing_manifest_file_is_rejected(self):
        self.add_assets("logo")
        record = self.manifest["assets"][0]
        self.manifest["assets"].append(record.copy())
        self.save_manifest()
        self.assert_rejected(self.run_verifier(), "Duplicate manifest filename")
        self.manifest["assets"].pop()
        self.save_manifest()
        (self.asset_dir / "logo.png").unlink()
        self.assert_rejected(self.run_verifier(), "missing: ['logo.png']")

    def test_asset_bytes_must_match_manifest_metadata(self):
        self.add_assets("logo")
        record = self.manifest["assets"][0]
        for key, value, reason in (
            ("width", 5, "unexpected dimensions"),
            ("height", 2, "unexpected dimensions"),
            ("alpha", False, "unexpected PNG alpha channel metadata"),
            ("alpha", 1, "unexpected PNG alpha channel metadata"),
            ("sha256", "0" * 64, "wrong SHA-256"),
            ("generated_with", "unknown", "must record @Images"),
            ("alt", " ", "missing alt"),
            ("source", "", "missing source"),
            ("status", "", "missing status"),
            ("role", "", "missing role"),
        ):
            with self.subTest(key=key, value=value):
                original = record[key]
                record[key] = value
                self.save_manifest()
                self.assert_rejected(self.run_verifier(), reason)
                record[key] = original

    def test_png_dimensions_require_json_integers(self):
        self.add_assets("logo")
        record = self.manifest["assets"][0]
        for key, invalid in (("width", 4.0), ("height", 1.0), ("height", True),
                             ("width", "4"), ("height", None)):
            with self.subTest(field=key, invalid=invalid):
                self.manifest["assets"][0] = {**record, key: invalid}
                self.save_manifest()
                self.assert_rejected(self.run_verifier(), "PNG dimensions must be integers")
        for field in ("width", "height"):
            with self.subTest(missing=field):
                self.manifest["assets"][0] = {key: value for key, value in record.items() if key != field}
                self.save_manifest()
                self.assert_rejected(self.run_verifier(), "PNG dimensions must be integers")
        self.manifest["assets"][0] = record
        self.save_manifest()
        self.assert_accepted(self.run_verifier())

    def test_blank_license_fails(self):
        (self.kit / "LICENSE").write_text(" \n", encoding="utf-8")
        self.assert_rejected(self.run_verifier(), "LICENSE file is empty")

    def test_linked_license_fails_even_when_target_is_readable(self):
        license_path = self.kit / "LICENSE"
        target = self.kit / "license-source"
        license_path.rename(target)
        self.symlink_or_skip(license_path, target)
        self.assert_rejected(self.run_verifier(), "Missing regular brand identity LICENSE")

    def test_linked_png_cannot_satisfy_registration(self):
        self.add_assets("logo")
        logo = self.asset_dir / "logo.png"
        target = self.kit / "logo-source"
        logo.rename(target)
        self.symlink_or_skip(logo, target)
        self.assert_rejected(self.run_verifier(), "Missing regular PNG: logo.png")

    def symlink_or_skip(self, link, target):
        try:
            link.symlink_to(target)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"Symlink creation unavailable: {error}")

    def test_missing_title_fails(self):
        self.brief.write_text("A brief with its title removed.\n", encoding="utf-8")
        self.assert_rejected(self.run_verifier(), "brief.md: missing title")

    def test_percent_encoded_local_link_with_fragment(self):
        (self.brief.parent / "work sample.md").write_text("# Evidence\n", encoding="utf-8")
        self.add_link("work%20sample.md#evidence")
        self.assert_accepted(self.run_verifier())

    def test_remote_link_and_fragment_only_are_not_resolved_as_files(self):
        self.add_link("https://example.invalid/evidence")
        self.add_link("#product")
        self.assert_accepted(self.run_verifier())

    def test_missing_and_outside_repository_links_are_rejected(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        content = self.brief.read_text(encoding="utf-8")
        for target in ("missing.md", "../../docs/missing.md", "../../../outside.md",
                       "%2e%2e/%2e%2e/%2e%2e/outside.md"):
            with self.subTest(target=target):
                self.brief.write_text(content, encoding="utf-8")
                self.add_link(target)
                self.assert_rejected(self.run_verifier(), target)

    def test_resolved_symlink_cannot_leave_repository(self):
        outside = self.root.parent / "outside.md"
        outside.write_text("# Outside\n", encoding="utf-8")
        self.symlink_or_skip(self.brief.parent / "shortcut.md", outside)
        self.add_link("shortcut.md")
        self.assert_rejected(self.run_verifier(), "shortcut.md")


class HandoffIssue13(AdoptedKit):
    def assert_approval_required(self, logo_status, wordmark_status):
        self.add_assets("logo", "wordmark")
        for asset, status in zip(self.manifest["assets"], (logo_status, wordmark_status)):
            asset["status"] = status
        self.save_manifest()
        self.assert_accepted(self.run_verifier())
        self.assert_rejected(self.run_verifier("--ready-for-handoff"), "status 'approved'")

    def test_draft_only_cannot_be_handed_off(self):
        self.assert_approval_required("draft", "draft")

    def test_test_only_cannot_be_handed_off(self):
        self.assert_approval_required("test", "test")

    def test_approved_logo_does_not_make_a_draft_wordmark_ready(self):
        self.assert_approval_required("approved", "draft")

    def test_approved_wordmark_does_not_make_a_test_logo_ready(self):
        self.assert_approval_required("test", "approved")

    def test_draft_can_coexist_with_approved_handoff_assets(self):
        self.add_assets("logo", "wordmark")
        filename, payload = "logo-draft.png", rgba_pattern()
        (self.asset_dir / filename).write_bytes(payload)
        self.manifest["assets"].append(asset_record(filename, payload, role="logo", status="draft"))
        self.save_manifest()
        self.assert_accepted(self.run_verifier("--ready-for-handoff"), "3 PNGs")


class EvidenceLinkIssue14(AdoptedKit):
    def test_existing_evidence_in_adopting_repository_is_allowed(self):
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "evidence.md").write_text("# Product evidence\n", encoding="utf-8")
        (docs / "research notes.md").write_text("# Research\n", encoding="utf-8")
        self.add_link("../../docs/evidence.md")
        self.add_link("../../docs/research%20notes.md#research")
        self.assert_accepted(self.run_verifier())


if __name__ == "__main__":
    unittest.main()
