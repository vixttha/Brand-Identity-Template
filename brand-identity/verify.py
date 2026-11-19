"""Check the portable brand kit and its registered PNG exports."""

import hashlib
import json
import struct
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

KIT = Path(__file__).resolve().parent
ASSETS = KIT / "09-assets"
REQUIRED_DOCS = (
    "README.md", "01-strategy/brief.md", "02-naming/naming.md",
    "03-messaging/voice.md", "04-logo/logo.md", "05-wordmark/wordmark.md",
    "06-visual-system/system.md", "07-applications/applications.md",
    "08-review/review.md", "09-assets/README.md",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_docs():
    for relative in REQUIRED_DOCS:
        source = KIT / relative
        content = source.read_text(encoding="utf-8")
        require(content.startswith("# "), f"{relative}: missing title")
        for reference in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", content):
            target = urlsplit(reference)
            if target.scheme or target.netloc or not target.path:
                continue
            destination = (source.parent / unquote(target.path)).resolve()
            require(destination.is_relative_to(KIT) and destination.exists(),
                    f"{relative}: missing or external local path {target.path}")


def check_png(asset):
    name = asset["file"]
    require(name == Path(name).name and name.endswith(".png"), f"Invalid asset path: {name}")
    file = ASSETS / name
    require(file.is_file() and not file.is_symlink(), f"Missing regular PNG: {name}")
    payload = file.read_bytes()
    require(payload.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR")
            and len(payload) >= 45 and payload.endswith(b"IEND\xaeB\x60\x82"),
            f"{name}: invalid PNG header or ending")
    width, height, _, color_type = struct.unpack(">IIBB", payload[16:26])
    require((width, height) == (asset["width"], asset["height"]) and min(width, height) > 0,
            f"{name}: unexpected dimensions {width}x{height}")
    require(isinstance(asset["alpha"], bool) and asset["alpha"] == (color_type in (4, 6)),
            f"{name}: unexpected PNG alpha channel metadata")
    require(hashlib.sha256(payload).hexdigest() == asset["sha256"], f"{name}: wrong SHA-256")
    require(asset["generated_with"] == "@Images", f"{name}: must record @Images generation")
    for key in ("role", "alt", "source", "status"):
        require(isinstance(asset[key], str) and asset[key].strip(), f"{name}: missing {key}")
    print(f"{name}: {width}x{height}, alpha channel {asset['alpha']}, SHA-256 verified")


def main():
    check_docs()
    inventory = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    require(inventory["kit_version"] == "v0.0.1", "Unexpected kit version")
    kind = inventory["kind"]
    require(kind in {"template", "project"}, f"Invalid kit kind: {kind}")
    assets = inventory["assets"]
    names = {asset["file"] for asset in assets}
    require(len(names) == len(assets), "Duplicate manifest filename")
    require(names == {path.name for path in ASSETS.glob("*.png")}, "PNG directory and manifest differ")
    if kind == "project":
        require({"logo", "wordmark"} <= {asset["role"] for asset in assets},
                "Project kit needs both logo and wordmark PNGs")
    for asset in assets:
        check_png(asset)
    print(f"Verified {kind} kit: {len(REQUIRED_DOCS)} documents and {len(assets)} PNGs")


if __name__ == "__main__":
    main()
