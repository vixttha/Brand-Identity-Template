# Brand Identity Template Test Vault

This branch stages the latest merged Lydite Test Vault starter, **v0.0.3**, from [the pinned upstream starter](https://github.com/vixttha/Lydite-Test-Vault-Template/tree/fe7b00aa17862d7a01dfd15481594be837bc6d9f/starter). The upstream [version manifest](https://github.com/vixttha/Lydite-Test-Vault-Template/blob/fe7b00aa17862d7a01dfd15481594be837bc6d9f/versions/manifest.json) and [public validation run](https://github.com/vixttha/Lydite-Test-Vault-Template/actions/runs/44475200133) identify the source. Lydite's [license](LICENSE) accompanies the copied files.

## Prepared for test planning

- [Cases](cases.md) is an empty project catalog.
- [Case and run receipt](case-and-receipt.md) defines what each result should record.
- [Execution evidence](evidence.md), [catalog validator](validate_catalog.py), and [receipt verifier](verify_receipts.py) supply the starter's validation tools.
- [Workflow template](templates/test-vault.yml) preserves the original GitHub Actions recipe outside the active workflows directory.
- [Changelog](CHANGELOG.md) and [upgrade notes](UPGRADE.md) describe this starter version.

The version's catalog validator expects at least one real case. Once cases are planned and entered, run `python3 test-vault/validate_catalog.py` from the repository root. The source starter's example cases, language demos, and sample tests remain available upstream. The project can choose test languages, cases, and runner wiring when test planning begins.
