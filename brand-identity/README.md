# Brand identity kit

A workspace for a project's look, language, and public identity. The owner directs the art. The agent researches, draws, revises, exports, and documents the assets.

| Folder | Contents |
| --- | --- |
| [Strategy](01-strategy/brief.md) | Product, audience, first surface, comparable references, and creative brief |
| [Naming](02-naming/naming.md) | Product name, aliases, casing, pronunciation, and collision research |
| [Voice and slogan](03-messaging/voice.md) | Slogan, short descriptor, tone, and claims |
| [Logo](04-logo/logo.md) | Symbol, silhouette, clear space, variants, and minimum size |
| [Wordmark](05-wordmark/wordmark.md) | Lettering, spelling, spacing, and logo lockup |
| [Visual system](06-visual-system/system.md) | Color, typography, layout, iconography, and imagery |
| [Applications](07-applications/applications.md) | UI, README, repository avatar, social, and accessible usage |
| [Review](08-review/review.md) | Visual checks, source/rights records, decisions, and rollout |
| [Assets](09-assets/README.md) | PNG exports and [asset manifest](09-assets/manifest.json) |

## Working session

1. Capture the owner's audience, practical use, visual references, and dislikes in the brief. Write success checks for the first place the brand will appear.
2. Develop a few visually distinct ideas when the brief leaves the direction open. Show them in the same size and context. Ask the owner to choose the direction or identify the change they want. The owner can describe feedback in ordinary terms, such as whether the silhouette feels too busy at icon size.
3. Generate or refine every proposed brand image with **@Images** (ChatGPT image generation). Deliver PNG exports and keep the image-generation source record. If image generation is unavailable, record the blocker and keep the image item pending.
4. Check spelling, optical spacing, meaningful small sizes, light and dark surfaces, and single-color reproduction where needed. Show any changes beside the previous draft. Use one recorded accent and a clear shape hierarchy until a second accent serves a specific purpose.
5. Register each file in the manifest and record the owner's decisions. Keep draft filenames distinct from approved assets. Apply the approved kit only to the surfaces the owner authorizes.

The design review can be run from this folder. `python brand-identity/verify.py` checks the kit inventory and PNG metadata from the repository root. PNG structure checks and visual acceptance have separate outcomes.
