"""Build the branding graph with this repository's pinned Graphify HQ tooling."""

import asyncio
import hashlib
import json
import os
from importlib.metadata import version
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(".graphify-hq/tools/graphify").resolve()))
from version_maps import LINK, blob_sha1, prose_lines, reference_path, verify_mcp
from graphify.build import build_from_json
from graphify.export import to_json

OUTPUT = Path("brand-graph")
SCOPE = "brand-kit-markdown-and-registered-pngs"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
if HEAD != os.environ["BRAND_CHECKOUT_SHA"]:
    raise ValueError("Brand graph checkout does not match the requested SHA")


def tracked_bytes(path):
    return subprocess.check_output(["git", "show", f"{HEAD}:{path}"])


def graph_node(key, label, path, kind):
    return {"id": key, "label": label, "file_type": kind,
            "source_file": path, "source_location": "L1" if kind == "document" else None}


paths = subprocess.check_output(["git", "ls-files", "-z", "brand-identity"], text=True).split("\0")
docs = {path: tracked_bytes(path) for path in sorted(paths) if path.endswith(".md")}
inventory = json.loads(tracked_bytes("brand-identity/09-assets/manifest.json"))
assets = {"brand-identity/09-assets/" + asset["file"]: asset for asset in inventory["assets"]}
nodes = {
    path: graph_node("document:" + path, path, path, "document")
    for path in docs
}
nodes.update({path: graph_node("asset:" + path, asset["role"], path, "concept")
              for path, asset in assets.items()})
edges = []
for path, data in docs.items():
    destinations = {
        reference_path(path, raw)
        for _, line in prose_lines(data.decode("utf-8"))
        for raw in LINK.findall(line.replace("![", "["))
    }
    for dest in sorted(dest for dest in destinations if dest in nodes and dest != path):
        edges.append({"source": nodes[path]["id"], "target": nodes[dest]["id"],
                      "source_file": path, "relation": "links_to",
                      "confidence": "EXTRACTED", "confidence_score": 1.0, "weight": 1.0})

graph = build_from_json({"nodes": list(nodes.values()), "edges": edges}, directed=True, dedup=False)
graph.graph.update(scope=SCOPE, kit_version=inventory["kit_version"])
OUTPUT.mkdir(exist_ok=True)
graph_path = OUTPUT / "graph.json"
to_json(graph, {0: list(graph)}, str(graph_path), built_at_commit="")
receipt = {"source_commit": HEAD, "source_ref": os.environ["BRAND_SOURCE_REF"],
           "scope": SCOPE, "graphify_version": version("graphifyy"),
           "graph_sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
           "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(),
           "documents": {path: blob_sha1(data) for path, data in docs.items()},
           "assets": {path: hashlib.sha256(tracked_bytes(path)).hexdigest() for path in assets}}
asyncio.run(verify_mcp(graph_path, receipt))
receipt["mcp_read_back"] = "pass"
(OUTPUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
