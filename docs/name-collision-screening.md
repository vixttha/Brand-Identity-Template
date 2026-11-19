# Proposal for screening brand names

Add a repeatable public search to the naming step in the Brand Identity Template. A maintainer should be able to compare candidates before choosing a name, see exactly what each candidate is connected to, and revisit the same checks before a public launch. The [GEvidence case study](research/gevidence-public-name-screen.md) shows why this matters. Three GitHub listings represent two implementations of the same ESG verification concept. A company in a different field uses the exact-match .com domain.

## What a maintainer provides

- The exact candidate spelling, explicit aliases, and any intended package, domain, repository, or account names.
- The project category, a brief description of what it does, who it serves, and launch markets. This context is used to review overlap.
- Known first-party public URLs or stable repository IDs, so the project's own listings can be reported separately.

Keep the naming record in [the existing kit](../brand-identity/02-naming/naming.md). Link it to a dated screening report. Attach the selected candidate's review decision to that report so a later run can show what changed since the decision.

## What can run mechanically

| Check | Evidence to return |
| --- | --- |
| Candidate variants | Keep the original label. Generate case-folded and joined, spaced, or hyphenated forms from explicit aliases and word boundaries. Record which form produced each result. Use near matches only as leads for review. |
| GitHub | Search public repository names and descriptions through the REST API. Record source IDs and canonical URLs. Inspect relevant project titles or README evidence for a branded use. Group identical commits or verified shared origins while preserving every listing. |
| Package registries | Perform exact lookups in the intended distribution channels. Report an existing listing, a verified registry no-hit, an incomplete response, or an unavailable source. A package no-hit applies only to that registry and identifier. |
| Domains | Resolve the authoritative RDAP service from IANA's bootstrap data. Record registered domains and distinguish a registry 404 from transport errors. Where useful, cite who uses the public site separately from the registration response. |
| Web, marketplaces and accounts | Accept cited manual findings and add adapters only for documented official interfaces with suitable access. Record the query and coverage, even when a source was skipped. |
| Trademark sources | Record any manually reviewed registry result with the jurisdiction, mark, status, goods or services, date, and official record URL. Link to the appropriate registries for markets in scope. Similarity and clearance require contextual review. |

## What the review should show

- A candidate report and diff against the previous approved baseline. Show identifiers, public URLs, observed and changed dates, the type of match, the source's coverage status, and why the result was included.
- Distinguish **matching name and overlapping audience**, **matching name in another field**, **similar name or related product**, **identifier already in use**, and **incidental text**. Keep name similarity, product or audience overlap, and launch-channel impact visible as separate judgments.
- Preserve the source evidence for each group. A duplicate listing can affect search visibility even when it adds no independent implementation. A domain hit and homepage may describe the same use. A first-party result gets its own label. A string inside a PDF, code field, or extracted affiliation remains incidental unless a primary source shows brand use.
- Give the maintainer a decision record with choices to keep, keep with caveats, investigate, or choose a different name, plus the reason. Reports describe observed conflicts and gaps. A low hit count cannot establish uniqueness or clearance.

## GitHub Actions proposal

Start with GitHub, npm, PyPI, RDAP, and a format for cited manual findings. Verify the classification and report generation against local fixtures on PRs. Add a separate maintainer-triggered live check on a standard public `ubuntu-latest` runner. Run it with read-only permissions, a bounded request budget, timeouts, and limited backoff for rate limits. Keep live results advisory. A rate limit, timeout, pagination cap, or GitHub `incomplete_results` sets the relevant source to partial or unavailable. Fixture tests can still fail on reproducible errors.

Publish a concise Actions job summary and compact JSON and Markdown artifacts. Include the template version, checkout SHA, run ID and attempt, observation time, exact queries, result statuses, and stable source IDs. Keep maintainer-approved baselines in an ordinary versioned file if comparisons need to outlive artifact retention. Omit private candidate lists, credentials, and raw registration contact data from public runs and artifacts. Keep local offline review available for confidential candidates. Live searches send the query to the selected provider even when run locally.

Later, optionally schedule a refresh for already-public candidates after a maintainer enables it. Scheduled runs execute from the default branch and GitHub may disable schedules on an inactive public repository. Keep manual runs available. The initial feature does not commit reports, file issues, or change a name automatically.

## Acceptance cases

| Fixture | Expected result |
| --- | --- |
| Case, space, and hyphen variants of a candidate | One candidate record with the exact input and traceable query variants. |
| Two repositories share a commit and a third has an independent implementation under the same label | Three source listings. One duplicate group and one distinct implementation. |
| The adopter's repo changes slug | Stable repo identity keeps its result first-party. An unrelated repo with a similar slug remains reviewable. |
| Exact name in another market, a similar name in the same category, and a matching text field | Three distinct findings with different reasons and no implied equal severity. |
| Registered `.com` and a provider returns a valid 404 for another TLD | Both observations retained, with accurate scope and no claim the second domain can be bought. |
| Registry 404, rate limit, timeout, and GitHub partial result | Separate statuses. A partial response never clears a prior hit or implies a source-wide no-hit. |
| Replaying an identical normalized snapshot | Same finding identities and ordering. Run metadata may change without producing a collision diff. |
| A new independent exact match appears | Report identifies the new source and marks it for review while preserving prior evidence. |

Sources for the proposed checks include [GitHub repository search](https://docs.github.com/en/rest/search/search#search-repositories), [Actions workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [public runner billing](https://docs.github.com/en/actions/concepts/billing-and-usage), [IANA RDAP bootstrap data](https://www.iana.org/assignments/rdap-dns/rdap-dns.xhtml), [USPTO clearance search guidance](https://www.uspto.gov/trademarks/search/comprehensive-clearance-search-similar-trademarks), and the [WIPO Global Brand Database](https://www.wipo.int/en/web/global-brand-database/index).
