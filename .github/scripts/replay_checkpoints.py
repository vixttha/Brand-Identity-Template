"""Replay the ten published snapshots and test their recorded acceptance checks."""
import io
import os
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import zipfile

BASE = "85545bce6b4372c321ba3072d37c0b9a9ba9a699"
CHECKPOINTS = [
    "a6240531b3127f19896515bce236f42887ac0141",
    "3fa643c966759ca5c9142ffff136cbc32976b3be",
    "d91b9f4e62fde959d9c8af790ad34c93ed66c4d6",
    "8608fed25b6fce6f5c1f13ee275d7773a6b9b126",
    "83331980bfed34c7eb20de4f6bad096446369f3f",
    "8dbf88cd724f4dd836b93798ec027b3ac83bd046",
    "84b94499985dc5efceb5e937b03edfa61717e44b",
    "7238cc2a9578f6cb14fe724f3bf412d82c15514f",
    "2c406be1375ce61e79d31b6bfd42f9e3edf4bd5f",
    "4b81280b90d974d0168c99adae041713c85d8ea1"
]
ROOT = Path.cwd()


def git(*args, **kwargs):
    return subprocess.check_output(["git", *args], cwd=ROOT, **kwargs)


def python(root, *args):
    subprocess.run([sys.executable, *args], cwd=root, check=True)


def check_readme(root):
    readme = (root / "README.md").read_text(encoding="utf-8")
    for path in re.findall(r"\[[^\]]+\]\((brand-identity/[^)]+)\)", readme):
        assert (root / path).is_file(), path
    assert "Add the kit to an existing project" in readme
    assert "standalone-checkpoints-v0.0.1.zip" in readme


def check_merged_base(root, worktree, sha):
    workflow = (root / ".github/workflows/brand-identity.yml").read_text(encoding="utf-8")
    step = workflow.split("      - name: Verify and record checkout provenance\n        run: |\n")[1]
    shell = textwrap.dedent(step.split("\n\n", 1)[0])
    env = os.environ | {
        "GIT_AUTHOR_NAME": "Verification", "GIT_AUTHOR_EMAIL": "verification@example.invalid",
        "GIT_COMMITTER_NAME": "Verification", "GIT_COMMITTER_EMAIL": "verification@example.invalid",
        "GITHUB_EVENT_NAME": "pull_request", "BRAND_PR_HEAD_SHA": sha,
        "GITHUB_STEP_SUMMARY": str(worktree.parent / "receipt.md"),
    }
    tree = git("rev-parse", f"{sha}^{{tree}}", text=True).strip()
    updated_base = git("commit-tree", tree, "-p", BASE, "-m", "Updated base fixture",
                       text=True, env=env).strip()
    stale_merge = git("commit-tree", tree, "-p", BASE, "-p", sha, "-m", "Earlier merge fixture",
                      text=True, env=env).strip()
    fresh_merge = git("commit-tree", tree, "-p", updated_base, "-p", sha, "-m", "Current merge fixture",
                      text=True, env=env).strip()
    git("worktree", "add", "--quiet", "--detach", str(worktree), stale_merge)
    try:
        env.update(BRAND_PR_BASE_SHA=updated_base, BRAND_CHECKOUT_SHA=stale_merge)
        stale = subprocess.run(["bash", "-eo", "pipefail", "-c", shell], cwd=worktree, env=env)
        assert stale.returncode != 0, "Stale merge receipt was accepted"
        subprocess.run(["git", "switch", "--quiet", "--detach", fresh_merge], cwd=worktree, check=True)
        env.update(BRAND_CHECKOUT_SHA=fresh_merge)
        subprocess.run(["bash", "-eo", "pipefail", "-c", shell], cwd=worktree, env=env, check=True)
        receipt = Path(env["GITHUB_STEP_SUMMARY"]).read_text(encoding="utf-8")
        assert all(value in receipt for value in (fresh_merge, updated_base, sha)), receipt
    finally:
        git("worktree", "remove", str(worktree))


def run():
    summary = []
    for index, sha in enumerate(CHECKPOINTS, 1):
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            root = temp / "source"
            with zipfile.ZipFile(io.BytesIO(git("archive", "--format=zip", sha))) as archive:
                archive.extractall(root)
            label = f"v0.0.1.{index}"
            parent = BASE if index == 1 else CHECKPOINTS[index - 2]
            assert git("rev-parse", f"{sha}^", text=True).strip() == parent
            subject = git("show", "-s", "--format=%s", sha, text=True).strip()
            assert subject.startswith(f"{label}:") and subject.endswith(f"(#{index + 1})"), subject
            git("diff", "--check", parent, sha)
            for path in root.rglob("*"):
                if path.is_file() and path.name != "LICENSE":
                    assert not re.search(r"\bBART\b|Blender-Agent", path.read_text(encoding="utf-8")), path
            assert (root / "brand-identity/LICENSE").is_file()
            if index >= 2:
                workflow = (root / ".github/workflows/brand-identity.yml").read_text(encoding="utf-8")
                assert "runs-on: ubuntu-latest" in workflow and "repository:" not in workflow
            if index >= 3:
                check_readme(root)
            print(f"::group::{label} {sha}", flush=True)
            python(root, "brand-identity/verify.py")
            python(root, "-m", "unittest", "discover", "-s", "brand-identity", "-v")
            if index >= 4:
                python(root, ".github/scripts/smoke_adoption.py")
            if index >= 9 and sys.platform == "linux":
                check_merged_base(root, temp / "merge-fixture", sha)
            print("::endgroup::", flush=True)
            summary.append(f"| {label} | `{sha}` | PASS |")
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as out:
        out.write("| Version | Exact commit | Result |\n| --- | --- | --- |\n")
        out.write("\n".join(summary) + "\n")


if __name__ == "__main__":
    run()
