"""Known pixel patterns for testing the verifier and an independent browser decoder."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunk(kind, data):
    checksum = zlib.crc32(kind + data)
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", checksum)


def png(width, height, depth, color, scanlines, *, metadata=(), interlace=0):
    header = struct.pack(">IIBBBBB", width, height, depth, color, 0, 0, interlace)
    parts = [(b"IHDR", header), *metadata, (b"IDAT", zlib.compress(scanlines)), (b"IEND", b"")]
    return SIGNATURE + b"".join(chunk(kind, data) for kind, data in parts)


def asset_record(filename, payload, *, role="logo", width=4, height=1, alpha=True,
                 status="approved"):
    return {
        "file": filename,
        "role": role,
        "alt": f"Synthetic {role} test pattern",
        "width": width,
        "height": height,
        "alpha": alpha,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "generated_with": "@Images",
        "source": "Synthetic test fixture, not production artwork",
        "status": status,
    }


def rgba_pattern():
    # Opaque red, fully transparent green, half-alpha blue, opaque green.
    return png(4, 1, 8, 6, bytes([0, 255, 0, 0, 255, 0, 255, 0, 0,
                                 0, 0, 255, 128, 0, 255, 0, 255]))


def write_browser_inputs(kit):
    indexed = png(4, 1, 2, 3, bytes([0, 0x1B]), metadata=(
        (b"PLTE", bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255])),
        (b"tRNS", bytes([255, 0, 128])),
    ))
    grayscale = png(4, 1, 8, 4, bytes([0, 0, 255, 64, 0, 128, 128, 255, 255]))
    rgb = png(4, 1, 8, 2, bytes([0, 255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 255]))
    patterns = (
        ("rgba.png", rgba_pattern(), True, "logo"),
        ("indexed.png", indexed, False, "wordmark"),
        ("grayscale-alpha.png", grayscale, True, "logo"),
        ("rgb.png", rgb, False, "wordmark"),
    )
    asset_dir = kit / "09-assets"
    manifest_path = asset_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # The caller supplies a disposable release checkout with its real assets directory.
    if manifest["kind"] != "template" or manifest["assets"]:
        raise ValueError("Browser fixtures require a clean template copy")
    manifest["kind"] = "project"
    for name, payload, alpha, role in patterns:
        (asset_dir / name).write_bytes(payload)
        manifest["assets"].append(asset_record(name, payload, alpha=alpha, role=role))
    write_json(manifest_path, manifest)


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kit", type=Path, help="Disposable copy of the kit")
    args = parser.parse_args()
    write_browser_inputs(args.kit)


if __name__ == "__main__":
    main()
