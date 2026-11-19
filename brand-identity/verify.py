"""Check the portable brand kit and its registered PNG exports."""

import argparse
import hashlib
import json
import struct
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re

KIT = Path(__file__).resolve().parent
ASSETS = KIT / "09-assets"
DECISION = KIT / "01-strategy" / "creative-decision.json"
WEIGHTS = {"brand_fit": 35, "artistic_character": 25,
           "distinctiveness": 25, "versatility": 15}
REQUIRED_DOCS = (
    "README.md", "AGENTS.md", "01-strategy/brief.md", "01-strategy/creative-direction.md",
    "01-strategy/meaning-method.md",
    "02-naming/naming.md",
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


def require_text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"Missing {label}")


def check_meanings(option, label):
    meanings = option.get("meanings")
    require(isinstance(meanings, list) and len(meanings) >= 3,
            f"{label}: record at least three meanings")
    required_layers = {"product", "audience", "principle"}
    layers = set()
    readings = set()
    for reading in meanings:
        require(isinstance(reading, dict), f"{label}: each meaning must be a record")
        layer = reading.get("layer")
        require(isinstance(layer, str) and layer in required_layers,
                f"{label}: invalid meaning layer")
        for key in ("detail", "meaning", "anchor"):
            require_text(reading.get(key), f"{label} meaning {key}")
        normalized = " ".join(reading["meaning"].casefold().split())
        require(normalized not in readings, f"{label}: meanings must be distinct")
        readings.add(normalized)
        layers.add(layer)
    require(layers == required_layers, f"{label}: cover product, audience, and principle")


def check_shortlist(options, label, minimum, distinct_field):
    require(isinstance(options, list) and len(options) >= minimum,
            f"{label}: record at least {minimum} options")
    seen_ids = set()
    seen_values = set()
    for option in options:
        require(isinstance(option, dict), f"{label}: each option must be a record")
        identity = option.get("id")
        require_text(identity, f"{label} option ID")
        require(identity not in seen_ids, f"{label}: duplicate option ID {identity}")
        seen_ids.add(identity)
        value = option.get(distinct_field)
        require_text(value, f"{label} {identity} {distinct_field}")
        normalized = " ".join(value.casefold().split())
        require(normalized not in seen_values, f"{label}: options must be distinct")
        seen_values.add(normalized)
        check_meanings(option, f"{label} {identity}")


def check_meaning_shortlists(decision):
    locked_name = decision.get("existing_name_lock")
    if locked_name is not None:
        require_text(locked_name, "existing product-name decision reference")
    names = decision.get("names", {})
    require(isinstance(names, dict), "Record proposed product and wordmark names")
    options = decision.get("name_options")
    check_shortlist(options, "Project names", 1 if locked_name else 2, "text")
    check_shortlist(decision.get("concepts"), "Logos", 3, "example")
    check_shortlist(decision.get("slogan_options"), "Slogans", 2, "text")
    wordmarks = decision.get("wordmark_options")
    check_shortlist(wordmarks, "Wordmarks", 2, "treatment")
    for option in wordmarks:
        require_text(option.get("text"), "exact wordmark option text")
    require(any(option["text"] == names.get("product") for option in options),
            "Include the exact proposed product name in the name shortlist")
    require(any(option["text"] == names.get("wordmark") for option in wordmarks),
            "Include the exact proposed wordmark text in the wordmark shortlist")


def check_artwork_gate(decision):
    initial = decision.get("initial_category")
    require_text(initial, "initial logo category")
    require_text(decision.get("art_style"), "lead art style")

    category_fit = decision.get("category_fit", {})
    require(isinstance(category_fit, dict) and initial in category_fit and len(category_fit) >= 2,
            "Screen the initial category and at least one alternative")
    for category, assessment in category_fit.items():
        require_text(category, "screened category")
        require(isinstance(assessment, dict) and type(assessment.get("fits")) is bool,
                f"{category}: record the fit decision")
        require_text(assessment.get("reason"), f"{category} fit rationale")

    concepts = decision.get("concepts", [])
    require(isinstance(concepts, list) and len(concepts) >= 3, "Record at least three concept examples")
    totals = {}
    examples = set()
    for concept in concepts:
        require(isinstance(concept, dict), "Each concept must be a record")
        identity = concept.get("id")
        require_text(identity, "concept ID")
        require(identity not in totals, f"Duplicate concept ID: {identity}")
        category = concept.get("category")
        require_text(category, f"{identity} category")
        require(category_fit.get(category, {}).get("fits"), f"{identity}: category must fit the brief")
        for field in ("art_style", "example", "rationale"):
            require_text(concept.get(field), f"{identity} {field}")
        example = " ".join(concept["example"].casefold().split())
        require(example not in examples, f"{identity}: concept example must be distinct")
        examples.add(example)

        scores = concept.get("scores", {})
        require(isinstance(scores, dict) and set(scores) == set(WEIGHTS) and all(
            type(score) is int and 1 <= score <= 5 for score in scores.values()
        ), f"{identity}: score each criterion with an integer from 1 through 5")
        totals[identity] = sum(scores[key] * weight for key, weight in WEIGHTS.items())

    selected = decision.get("selected_concept")
    require_text(selected, "selected concept")
    require(totals.get(selected) == max(totals.values()), "Select a highest-scoring concept")
    require_text(decision.get("selection_reason"), "selection rationale")

    names = decision.get("names", {})
    require(isinstance(names, dict), "Record proposed product and wordmark names")
    confirmation = decision.get("confirmation")
    require(isinstance(confirmation, dict), "Owner name confirmation is required before artwork")
    for key in ("product", "wordmark"):
        require_text(names.get(key), f"proposed {key} name")
        require(names[key] == confirmation.get(key), f"Confirm the exact {key} name before artwork")
    require_text(confirmation.get("reference"), "owner confirmation reference")
    check_meaning_shortlists(decision)


def validate_production(kind, assets, ready_for_artwork, decision):
    if kind == "template":
        require(not assets and not ready_for_artwork, "Start a project kit before adding brand artwork")
    if assets or ready_for_artwork or decision.get("confirmation") is not None:
        check_artwork_gate(decision)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ready-for-artwork", action="store_true",
                        help="require a scored direction and explicit owner name confirmation")
    parser.add_argument("--check-shortlists", action="store_true",
                        help="check the written options before requesting confirmation")
    args = parser.parse_args()
    check_docs()
    inventory = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    require(inventory["kit_version"] == "v0.0.1", "Unexpected kit version")
    kind = inventory["kind"]
    require(kind in {"template", "project"}, f"Invalid kit kind: {kind}")
    assets = inventory["assets"]
    names = {asset["file"] for asset in assets}
    require(len(names) == len(assets), "Duplicate manifest filename")
    require(names == {path.name for path in ASSETS.glob("*.png")}, "PNG directory and manifest differ")
    decision = json.loads(DECISION.read_text(encoding="utf-8"))
    require(isinstance(decision, dict), "The creative decision must be a record")
    if args.check_shortlists:
        check_meaning_shortlists(decision)
        print("Four shortlists with distinct anchored meanings verified")
    validate_production(kind, assets, args.ready_for_artwork, decision)
    if assets:
        require({"logo", "wordmark"} <= {asset["role"] for asset in assets},
                "A populated project kit needs both logo and wordmark PNGs")
    if args.ready_for_artwork:
        print("Creative decision and owner name confirmation recorded")
    for asset in assets:
        check_png(asset)
    print(f"Verified {kind} kit: {len(REQUIRED_DOCS)} documents and {len(assets)} PNGs")


if __name__ == "__main__":
    main()
