# Meaning-led brand identity

A meaningful identity makes a deliberate choice in a shape, word, or letter that recalls something specific about the project. Start with one literal product fact, one consequence for the people who use it, and one principle the project practices. Find a form that carries all three. A small brand mark should still read as a coherent shape when the audience sees it before hearing the story.

## Collect the source material

- What does the project make possible? Identify an operation, artifact or decision and record its source.
- What experience or tension does it change for the people using it? Record an example, research finding or owner answer.
- What principle explains how it does that work? Find a real practice, constraint or trade-off that supports the interpretation.
- What are the exact naming constraints and first usage surfaces? Ask the owner about existing locked strings and look at the size, contrast and context the work must serve.

## Build four independent shortlists

| List | What the option describes | Where a meaning can live |
| --- | --- | --- |
| Project names | Exact spelling, origin, pronunciation and likely ambiguity | A root, the relationship between words, or a documented allusion. Verify linguistic and cultural claims. |
| Logos | Silhouette, category, art style and the feature that will survive at small sizes | A contour, opening, junction, letterform or relationship between masses. |
| Slogans | Exact line and the promise it can make honestly | A verb, a deliberate contrast in the sentence, a pause or a memorable turn of phrase. |
| Wordmarks | Exact letters and a distinct lettering treatment | A counter, terminal, rhythm, spacing decision or custom letter joint. Two treatments may use the same locked text. |

Write at least two options for each list, with at least three scored logo concepts as required by the creative workflow. If the owner has already locked a product name, record the existing name as one option and cite that decision. Each option has at least three **distinct meanings**, one each for product, audience, and principle. For every meaning, show the perceivable **detail**, what it **means**, and its **anchor**. An anchor can be a project source, a publishable owner decision, or documented research. Label artistic interpretations as interpretations. Link references when their origin matters.

## Review the connections

1. **Remove the detail.** Omit the chosen contour, word or letter feature and identify what meaning disappears. If the explanation works unchanged, make the connection more concrete.
2. **Swap the project.** Try the option on an unrelated product. Identify the reading that stops making sense. If the whole rationale travels intact, return to project evidence.
3. **Strip the finish.** Evaluate the symbol in one color and at the intended minimum size. Read copy aloud and test the wordmark's exact spelling without color. Revise any option whose idea depends on effects or a paragraph of explanation.
4. **Read without the rationale.** Record what a new viewer is likely to perceive first, what the deeper reading adds, and the most plausible misread. Score logo concepts on the [existing rubric](creative-direction.md). Present the best candidates and the trade-offs before the owner selects or confirms anything.

## Record format

Use the [creative decision](creative-decision.json). The four lists are `name_options`, `concepts` for logos, `slogan_options`, and `wordmark_options`. Use a unique `id` within each list. Names, slogans and wordmarks have `text`. Wordmarks also have `treatment`. Logo concepts retain their category, art style, example, rationale and scores.

Each option has a `meanings` list. Each entry has `layer` (`product`, `audience`, or `principle`), `detail`, `meaning`, and `anchor`. Include the chosen exact name and wordmark text in their lists. Use `existing_name_lock` only for a previously locked name, with a publishable reference. Exact owner confirmation for the artwork still follows the [creative direction workflow](creative-direction.md). Run `python3 brand-identity/verify.py --check-shortlists` to check the written options before asking for confirmation. A complete record documents the reasoning. The design review judges whether the reasons hold up.
