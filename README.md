# Brand Identity Template

Use the [brand identity kit](brand-identity/README.md) to develop your product's name, slogan, logo, wordmark, visual system and PNG assets. Start with your audience, the product's purpose and the first place the brand will appear.

## Add the kit to an existing project

1. Download the [v0.0.1 candidate ZIP](https://github.com/vixttha/Brand-Identity-Template/archive/refs/heads/standalone-checkpoints-v0.0.1.zip) and extract it. Copy the entire `brand-identity/` directory, including its license, into your repository. If that directory already exists, review the files before copying them.
2. Link `brand-identity/README.md` from your project's existing `AGENTS.md` or equivalent instructions, or point the agent directly to the [kit README](brand-identity/README.md).
3. Start the [creative brief](brand-identity/01-strategy/brief.md). Follow the [creative direction workflow](brand-identity/01-strategy/creative-direction.md) before generating artwork with @Images.
4. From your repository root, run `python3 brand-identity/verify.py`. On Windows, use `py -3 brand-identity/verify.py`. The verifier uses Python 3.10+ and its standard library.
