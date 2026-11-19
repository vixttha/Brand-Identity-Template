# Brand Identity Template Test Vault

This vault uses the copy-in starter from [Lydite Test Vault v0.0.4](https://github.com/vixttha/Lydite-Test-Vault-Template/releases/tag/v0.0.4). The adoption source is [the starter at the release commit](https://github.com/vixttha/Lydite-Test-Vault-Template/tree/87d25d80d3154d295052412b64b29a0f0f152c27/starter) (the upstream archive manifest tracks older starter versions). The starter's [license](LICENSE) accompanies the copied files.

| Suite | What it proves |
|---|---|
| Python | The adopted verifier's exit status, artwork and handoff gates, manifest and PNG integrity, evidence-link boundaries, and Lydite catalog and receipt verdicts. |
| JavaScript | Chromium decodes accepted PNG bytes and composites transparent pixels correctly over light and dark backgrounds. |
| Bash | The exact candidate commit and public ZIP URLs produce adoptable kits, adoption preserves an existing repository, and checkout receipts match actual Git commits and ordered PR parents. |

Use the [case catalog](cases.md) for the link to each assertion and the [active workflow](../.github/workflows/lydite-mechanical.yml) for public-runner coverage. The [case and receipt reference](case-and-receipt.md), [execution evidence guide](evidence.md), and [starter workflow](templates/test-vault.yml) remain available for recording further cases.

## Run locally

Run from the repository root. Commit tracked changes before running the browser receipt check. The full vault Python suite and receipt verifier require Python 3.12. The kit verifier has a separate Python 3.10 compatibility check.

```sh
python3 test-vault/validate_catalog.py
python3 -B -m unittest discover -s test-vault/tests -v
bash test-vault/tests/test_checkout.sh
bash test-vault/tests/test_candidate_archive.sh
bash test-vault/tests/adopt_archive.sh
npm --prefix test-vault/browser ci
node --test test-vault/browser/verify-results.unit.cjs
(cd test-vault/browser && npx playwright install --with-deps --only-shell chromium)
bash test-vault/tests/browser.sh
```

The adoption check needs Git, curl, unzip, tar and network access to the public GitHub archives. Run `bash test-vault/tests/adopt_archive.sh --candidate-only` to build and adopt the ZIP from your checked-out commit offline. For local browser runs with an already installed Chromium, set `BRAND_BROWSER_EXECUTABLE` to its absolute path before running the browser script.

The browser script uses a temporary copy of the kit. The verifier validates each PNG against the fixture manifest. Chromium consumes the same registered filenames. A Chromium receipt requires one passing result for each test in [the required test list](browser/required-tests.json). Update that list when adding or renaming a required browser test. The combined Lydite receipt binds both results to the clean checkout, the v2 case plan digest, and the shared PNG manifest digest. The browser tests use synthetic, known pixel values. Screenshots of approved artwork, minimum display sizes, official SVGs, and visual approval of lettering and lockups require project assets and owner decisions.

## Handoff and evidence-link regressions

Ordinary regression tests cover draft-only, test-only and mixed-status handoffs ([issue #13](https://github.com/vixttha/Brand-Identity-Template/issues/13)) and existing adopter-local evidence links ([issue #14](https://github.com/vixttha/Brand-Identity-Template/issues/14)).
