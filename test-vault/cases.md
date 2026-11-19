# Brand Identity Template test catalog

Each row states a distinct behavior and links to its assertions. Run commands, expected failures, and evidence limits are in the [vault README](README.md).

| Case | Area | Priority | Suggested implementation | Expected outcome |
|---|---|---|---|---|
| KIT-001 | Manifest | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | Unsupported kit kinds and versions fail. An empty adopted template can become a project inventory. |
| KIT-002 | Artwork | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | The template cannot enter artwork. An unconfirmed project can remain a work in progress. Stale confirmation blocks registered art. |
| KIT-003 | Scoring | P1 | [Python verifier CLI](tests/test_verifier_cli.py) | Weighted scoring rules out the lower total and permits either tied leader. Invalid concept IDs, categories, scores and required decision text fail. |
| KIT-004 | Handoff | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | An approved logo and wordmark pass. Omitting either role fails. Draft and test assets remain valid inventory. |
| KIT-005 | Handoff approval | P0 | [Python issue #13 regressions](tests/test_verifier_cli.py) | Draft-only, test-only and either mixed-status inventory should fail final handoff. Four expected failures reproduce [issue #13](https://github.com/vixttha/Brand-Identity-Template/issues/13). |
| KIT-006 | Inventory | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | Duplicate filenames or registered files missing from disk fail. |
| KIT-007 | Asset metadata | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | Dimensions, alpha-channel metadata and SHA-256 must agree with the file. Alt text, provenance, role and status must be present. |
| KIT-008 | License and docs | P1 | [Python verifier CLI](tests/test_verifier_cli.py) | Blank license or missing document title fails verification. |
| LINK-001 | Markdown links | P1 | [Python verifier CLI](tests/test_verifier_cli.py) | An encoded local path with a fragment passes. Web URLs and fragment-only links do not require local files. |
| LINK-002 | Repository boundary | P0 | [Python verifier CLI](tests/test_verifier_cli.py) | Missing local targets and paths that resolve outside the adopter, including a symlink where available, fail. |
| LINK-003 | Adopter evidence | P1 | [Python issue #14 regression](tests/test_verifier_cli.py) | An existing adopter-local evidence file should pass. One expected failure reproduces [issue #14](https://github.com/vixttha/Brand-Identity-Template/issues/14). |
| PNG-001 | Pixel encoding | P1 | [Python PNG parser](tests/test_png_encodings.py) | Opaque and alpha color types yield the right channel metadata. Packed rows and nontrivial Adam7 passes require the correct byte count. |
| PNG-002 | PNG headers | P0 | [Python PNG parser](tests/test_png_encodings.py) | Invalid dimensions, color type and bit depth fail. |
| PNG-003 | Palette | P0 | [Python PNG parser](tests/test_png_encodings.py) | Indexed PNGs require one well-formed palette of a size permitted by their bit depth. |
| PNG-004 | Image data | P0 | [Python PNG parser](tests/test_png_encodings.py) | Adjacent IDAT chunks decode together. Nonconsecutive chunks and extra compressed members fail. |
| PNG-005 | PNG framing | P0 | [Python PNG parser](tests/test_png_encodings.py) | Missing or truncated chunks, unexpected critical chunks and trailing bytes fail. Unknown ancillary chunks can be ignored. |
| PNG-010 | Browser decoding | P0 | [Python + JavaScript receipts](tests/png-browser-case.json) | The release verifier accepts a shared PNG inventory and Chromium decodes known RGBA, indexed, grayscale-alpha and RGB patterns at native size. Both receipts bind to the same manifest digest. |
| PNG-011 | Browser compositing | P1 | [JavaScript Playwright](browser/png.spec.cjs) | Transparent pixels reveal the light or dark background, semitransparent edges blend as expected, and opaque pixels retain their color. |
| ZIP-001 | Documented download | P0 | [Bash ZIP adoption](tests/adopt_archive.sh) | The advertised main ZIP really downloads and its entire kit matches a current main checkout. |
| ZIP-002 | Versioned download | P0 | [Bash ZIP adoption](tests/adopt_archive.sh) | The public v0.0.2 ZIP matches the pinned release commit's kit, including its license. |
| ZIP-003 | Fresh adoption | P0 | [Bash ZIP adoption](tests/adopt_archive.sh) | A released kit works from an existing adopter path containing spaces before and after changing the manifest to project mode. |
| ZIP-004 | Adoption boundaries | P0 | [Bash ZIP adoption](tests/adopt_archive.sh) | The original adopter files and Git HEAD are preserved, and the copied license matches the ZIP. |
| GIT-001 | Source checkout | P0 | [Bash Git checkout](tests/test_checkout.sh) | The actual source SHA passes. A stale SHA or head-only PR checkout fails. |
| GIT-002 | Combined checkout | P0 | [Bash Git checkout](tests/test_checkout.sh) | A real synthetic merge passes with its ordered current parents. Reversed or stale parents fail. |
| VAULT-001 | Catalog | P1 | [Python Lydite CLI](tests/test_vault_cli.py) | Escaped separators and fenced examples do not introduce phantom rows. Empty or malformed tables, duplicate IDs, invalid priorities and mismatched topics fail. |
| VAULT-002 | Receipt binding | P0 | [Python Lydite CLI](tests/test_vault_cli.py) | Both required receipts must match the selected catalog case, exact checkout, run, attempt and evidence digest. |
| VAULT-003 | Combined verdict | P0 | [Python Lydite CLI](tests/test_vault_cli.py) | Missing, duplicate, undeclared, malformed, failed, skipped or blocked receipts cannot satisfy an all-pass verdict. |
| VAULT-004 | Shared evidence | P0 | [Python Lydite CLI](tests/test_vault_cli.py) | Cases without shared evidence require null digests. Changed evidence fails verification of receipts from before the edit. |
