# Brand Identity Template v0.0.1

Use the [brand identity kit](brand-identity/README.md) to develop a product name, slogan, logo, wordmark, visual system, and assets for the places your audience will see them. The project owner directs the design. The agent researches, draws, revises, and exports the PNGs with **@Images**.

## Add the kit to an existing project

1. Download the [template branch ZIP](https://github.com/vixttha/Brand-Identity-Template/archive/refs/heads/Brand-Identity-template-v0.0.1.zip), or clone that branch. Copy the whole `brand-identity/` directory into your project and keep its `LICENSE`. If the project already has a directory with that name, review the files before combining them.
2. Add a link to `brand-identity/README.md` in the project's existing `AGENTS.md` or equivalent agent instructions. If the project has no agent instructions, point the agent directly to the kit README.
3. Start with the [creative brief](brand-identity/01-strategy/brief.md). Use the [asset manifest](brand-identity/09-assets/manifest.json) for PNGs and the [review record](brand-identity/08-review/review.md) for the owner's decisions. Keep drafts separate from approved exports.
4. Run `python3 brand-identity/verify.py` from your repository root. On Windows, `py -3 brand-identity/verify.py` runs the same check. The verifier uses the Python 3.10+ standard library and works with local, private, and public repositories.

For a filled example, see the [BART brand kit](https://github.com/vixttha/Brand-Identity-Template/tree/BART-Brand-Identity/brand-identity). Its Facet artwork is a rejected historical draft with project-specific reuse terms.

## Creative direction and confirmation

The [creative direction workflow](brand-identity/01-strategy/creative-direction.md) records the initial logo category, art style, category fit, rated examples, selected direction and exact owner-confirmed names before artwork. See the [BART audit and worked shortlist](docs/BART-creative-audit.md) for a pre-artwork example.

## Source and checks

The kit comes from the [original v0.0.1 snapshot](https://github.com/vixttha/Blender-Agent-Refinement-Toolkit/tree/7ba49fca6600598a1e75cffbd318b50bd881b953). The [source runner receipt](https://github.com/vixttha/Blender-Agent-Refinement-Toolkit/actions/runs/44478294653) records the original template checks.

The workflows in this repository validate the source branches on standard public GitHub-hosted runners. They test the local verifier after copying the kit into a separate repository and build a brand graph with pinned Graphify tooling. Adopting the kit requires only the `brand-identity/` directory.
