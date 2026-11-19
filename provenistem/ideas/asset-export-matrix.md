# Brand asset export matrix

[IDEA-000008](records/IDEA-000008.json) records the owner's request for four transparent PNGs and four transparent SVGs for every approved mark. The four treatments below are proposed for design review.

## Four treatments per asset

| Treatment ID | Artwork | Use on |
| --- | --- | --- |
| `color-on-light` | Full-color artwork tuned for contrast | White or pale surfaces |
| `color-on-dark` | Full-color artwork tuned for contrast | Dark or saturated surfaces |
| `mono-black` | Solid black artwork | Light surfaces and one-ink use |
| `mono-white` | Solid white artwork | Dark surfaces and reversed one-ink use |

Both file formats use a transparent canvas. The surface color describes where to place the art. Record any treatment that shares identical artwork with another treatment.

## Required and optional sets

| Approved asset | PNG | SVG | Total |
| --- | ---: | ---: | ---: |
| Logo symbol | 4 | 4 | 8 |
| Standalone wordmark | 4 | 4 | 8 |
| Primary logo and wordmark lockup | 4 | 4 | 8 |
| **Core set** | **12** | **12** | **24** |
| Each additional approved symbol, wordmark, or lockup | 4 | 4 | 8 more |

Use a horizontal layout as the starting proposal for the primary lockup. If both horizontal and stacked layouts are approved, the stacked lockup gets its own set and brings the total to **32**. A compact mark, emblem, or alternate wordmark also gets its own set when approved. Add raster widths or pixel-density variants separately from the four visual treatments.

## Naming and handoff

- Name files `<asset>--<treatment>.<ext>`. For example, `logo--color-on-light.png`, `wordmark--mono-white.svg`, and `lockup-horizontal--color-on-dark.svg`.
- Give each approved asset a master reference. Keep its geometry, exact wording, proportions, clear space, and layout consistent across format and treatment. Record intentional color or optical adjustments.
- Check each PNG for transparent pixels, native dimensions, and readable edges at the intended size. Give each SVG a suitable `viewBox`, retain intentional transparent areas, and make display lettering render consistently without depending on a visitor's fonts.
- Preview each format on its intended surface. Verify logo-only, wordmark-only, and lockup uses at their minimum intended sizes. Record intended backgrounds, export revision, and approval status in the handoff inventory.

This proposal is tracked alongside [cross-surface acceptance](records/IDEA-000003.json) and [vector delivery](records/IDEA-000004.json).
