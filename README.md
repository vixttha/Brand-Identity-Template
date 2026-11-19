# Brand Identity Template

Use the [brand identity kit](brand-identity/README.md) to develop your product's name, slogan, logo, wordmark, visual system and PNG assets. Start with your audience, the product's purpose and the first place the brand will appear.

## Add the kit to an existing project

1. Download the [meaning-led identity branch ZIP](https://github.com/vixttha/Brand-Identity-Template/archive/refs/heads/meaning-led-identity.zip) and extract it. Copy the entire `brand-identity/` directory, including its license, into your repository. If that directory already exists, review the files before copying them.
2. Link `brand-identity/AGENTS.md` from your project's existing agent instructions, or point the agent directly to the [kit operating instructions](brand-identity/AGENTS.md).
3. In the copied `brand-identity/09-assets/manifest.json`, change `"kind": "template"` to `"kind": "project"`. Leave `assets` empty until you register your exports.
4. Start the [creative brief](brand-identity/01-strategy/brief.md). Follow the [creative direction workflow](brand-identity/01-strategy/creative-direction.md) before generating artwork with @Images.
5. From your repository root, run `python3 brand-identity/verify.py`. On Windows, use `py -3 brand-identity/verify.py`. The verifier uses Python 3.10+ and its standard library.

## Install on a branch of your own project

From a clean checkout of your intended project base, run the following when `brand-identity/` is available for a new kit. If it already contains project files, compare the ZIP contents and adopt the changes one file at a time.

```sh
git fetch https://github.com/vixttha/Brand-Identity-Template.git meaning-led-identity
git switch -c brand-identity-work
git restore --source=FETCH_HEAD --staged --worktree -- brand-identity/
```

Keep the destination project's existing root instructions. For a brand session, point your agent to `brand-identity/AGENTS.md` and the project's brief. The [meaning method](brand-identity/01-strategy/meaning-method.md) defines the four required shortlists and how to review their reasoning. Review the staged copy, commit it to your branch, and push it to your own remote when ready.
