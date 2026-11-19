"""Exercise the documented adoption path in a disposable repository."""

import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
import zlib

SOURCE = Path(__file__).resolve().parents[2] / "brand-identity"
sys.path.insert(0, str(SOURCE))
from test_verify import scored_decision


def png_chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def write_record(path, record):
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def run():
    instructions = b"# Existing project instructions\n"
    readme = b"# Existing project README\n"
    with TemporaryDirectory() as temporary:
        consumer = Path(temporary)
        subprocess.run(["git", "init", "-q"], cwd=consumer, check=True)
        (consumer / "AGENTS.md").write_bytes(instructions)
        (consumer / "README.md").write_bytes(readme)
        def git(*args):
            subprocess.run(["git", *args], cwd=consumer, check=True)

        git("add", "AGENTS.md", "README.md")
        git("-c", "user.name=Template CI", "-c", "user.email=template-ci@example.invalid",
            "commit", "-qm", "Create synthetic host project")
        git("fetch", "--no-tags", str(SOURCE.parent), "HEAD")
        git("switch", "-c", "brand-identity-work")
        git("restore", "--source=FETCH_HEAD", "--staged", "--worktree", "--", "brand-identity/")
        kit = consumer / "brand-identity"
        command = [sys.executable, "brand-identity/verify.py"]
        subprocess.run(command, cwd=consumer, check=True)

        assets = kit / "09-assets"
        manifest_path = assets / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["kind"] = "project"
        write_record(manifest_path, manifest)
        decision_path = kit / "01-strategy" / "creative-decision.json"
        complete = scored_decision()
        draft = {**complete, "confirmation": None}
        write_record(decision_path, draft)
        subprocess.run([*command, "--check-shortlists"], cwd=consumer, check=True)
        pending = subprocess.run([*command, "--ready-for-artwork"], cwd=consumer,
                                 capture_output=True, text=True)
        assert pending.returncode and "Owner name confirmation is required" in pending.stderr
        write_record(decision_path, complete)
        subprocess.run([*command, "--ready-for-artwork"], cwd=consumer, check=True)

        # A transparent 1×1 test fixture exercises registration without production art.
        payload = (
            b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
            + png_chunk(b"IDAT", zlib.compress(b"\0" * 5))
            + png_chunk(b"IEND", b"")
        )
        for role in ("logo", "wordmark"):
            filename = f"test-{role}.png"
            (assets / filename).write_bytes(payload)
            manifest["assets"].append({
                "file": filename,
                "width": 1,
                "height": 1,
                "alpha": True,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "generated_with": "@Images",
                "role": role,
                "alt": f"Synthetic {role} fixture",
                "source": "Synthetic CI fixture that exercises the @Images inventory field",
                "status": "test",
            })
        write_record(manifest_path, manifest)
        subprocess.run(command, cwd=consumer, check=True)
        assert (consumer / "AGENTS.md").read_bytes() == instructions
        assert (consumer / "README.md").read_bytes() == readme
        assert (kit / "LICENSE").is_file()


if __name__ == "__main__":
    run()
