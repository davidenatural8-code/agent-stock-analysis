---
name: claude-pptx-skills
description: >-
  Use this skill for ANY task involving creating, editing, or adding content to a .pptx file -
  a new deck built from the design layer, editing an existing presentation, or a one-off tweak
  to a single slide such as adding an element, moving a chart, or changing a color. Also known as
  pptx-generation. Covers the semantic design layer (brand tokens: colors, typography, slide chrome,
  and chart styling recipes), composing slide arrangements with grid systems, and mandatory visual +
  conformance QA before delivery (check_file, check_design, render_qa).
---

# PPTX Generation & Editing

## Requirements
This skill's scripts need, on the host system:
- `python-pptx` (`pip install python-pptx --break-system-packages`), the only deck library used here
- `libreoffice` (provides the `soffice` binary, for headless rendering)
- `poppler-utils` (provides `pdftoppm`)

## Step 0: classify the request first
Before writing any code, decide which case this is. Most requests are case C, so don't over-engineer them.

- **A. New deck or new slides** → build from the design layer with `build.py`. Go to Workflow A.
- **B. Editing an existing .pptx substantially** (restructure, many slides) → open the file as-is, don't regenerate from scratch. Go to Workflow B.
- **C. A one-off tweak** ("add this element", "move that chart", "change this color") → no ceremony needed. Open the file, inspect the specific slide's shapes, make the minimal edit, re-render, done.

## Workflow A: new deck or new slides

Everything visual comes from the design layer. Do not invent a font, a color, a
chart's axis behaviour, or slide coordinates: read them from the tokens file, and
if something is genuinely missing, add it to the tokens file rather than to the
slide code.

### 1. Load the design layer
A tokens file under `design/` (e.g. `design/brand.tokens.json`), authored and
versioned by hand, independent of any one `.pptx`. If none exists for this brand,
write one following the schema below, and ask for real brand values rather than
inventing them.

Inspect what's in it before composing:
```bash
python scripts/tokens.py design/brand.tokens.json                 # whole resolved tree
python scripts/tokens.py design/brand.tokens.json charts.bar      # one chart recipe
python scripts/tokens.py design/brand.tokens.json type.title      # one text role
```

### 2. Separate the chrome from the arrangement

This distinction matters more than any other in this skill:

- **Chrome** (logo, where the title sits, footer, background, margins) is *design
  identity*. It is fixed for a deck, it lives in `layout.slide_type`, and you get
  it by naming a slide type. Never draw it by hand.
- **Arrangement** (how this slide's body is divided) is *content*. It varies with
  what the user asked for, so **compose it**. There is deliberately no catalogue
  of preset layouts to pick from: build the arrangement the request describes.

```python
import sys, os
# Add scripts directory (support relative, workspace, or global installation)
script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts") if "__file__" in locals() else "scripts"
if os.path.exists(script_dir):
    sys.path.insert(0, script_dir)
else:
    for p in [r"c:\PROJECT\Informes\.agents\skills\claude-pptx-skills\scripts", os.path.expanduser("~/.gemini/config/skills/claude-pptx-skills/scripts")]:
        if os.path.exists(p):
            sys.path.insert(0, p); break
from pptx import Presentation
import grid, build, tokens

tk  = tokens.load("design/brand.tokens.json")
prs = Presentation("templates/blank.pptx")

# chrome from the slide type; `body` is the box left to compose in
slide, body = build.new_slide(prs, tk, "content",
                              heading="Revenue by Region",
                              subtitle="Europe widened its lead every quarter",
                              footer_text="FY25 review")

# arrangement composed to fit the request, nested as deeply as needed
main, side = grid.cols(tk, body, weights=[0.62, 0.38])

build.card(slide, tk, main, title="Quarterly revenue ($M)")
chart = build.chart(slide, tk, "bar", build.chart_box(tk, main),
                    ["Q1", "Q2", "Q3", "Q4"],
                    {"Europe": [42, 48, 51, 60], "Americas": [30, 35, 33, 40]})
build.card(slide, tk, side, title="Key insight", body="...")

chart.value_axis.maximum_scale = 80        # raw python-pptx whenever you need it
prs.save("output/deck.pptx")
```

### 3. Splitting boxes (`grid.py`)

`grid.rows` and `grid.cols` take a box and return boxes. Every result can be split
again, so any arrangement is reachable by nesting. Three mutually exclusive ways
to divide:

```python
grid.cols(tk, box, n=3)                          # three equal columns
grid.cols(tk, box, weights=[0.6, 0.4])           # proportional
grid.rows(tk, box, sizes=[1.05, 0.95, "auto"])   # absolute inches; "auto" takes the rest
grid.pad(box, 0.2, top=0.3)                      # shrink a box inward
```

Gaps come from `layout.gap_in` automatically, so blocks never touch and never
overlap. Worked example, "a headline and three stats over a chart, with two
charts stacked on the right":

```python
left, right      = grid.cols(tk, body, weights=[0.6, 0.4])
head, stats, plot = grid.rows(tk, left, sizes=[1.05, 0.95, "auto"])
a, b, c           = grid.cols(tk, stats, n=3)
top, bottom       = grid.rows(tk, right, n=2)
```

### 4. Helpers

| Function | Purpose |
|---|---|
| `build.new_slide(prs, tk, type, heading=, subtitle=, footer_text=)` | slide + chrome; returns `(slide, body_box_or_None)` |
| `build.blank_slide(prs)` | a slide with no chrome at all |
| `build.text(slide, tk, role, content, box)` | textbox styled from `type.<role>`; `content` may be a list of paragraphs |
| `build.bullets(slide, tk, items, box)` | a bulleted list |
| `build.card(slide, tk, box, title=, body=)` | background block from `component.card` |
| `build.chart_box(tk, box)` | where a chart goes inside a titled card |
| `build.kpi(slide, tk, box, value, label)` | big number + caption |
| `build.chart(slide, tk, kind, box, categories, series, emphasize=, number_format=)` | a chart styled by `charts.<kind>` |

`series` is `{name: [values]}`; insertion order fixes color order. `emphasize=i`
highlights one category and mutes the rest, for when the story is one bar.
`number_format` overrides the recipe default, because decimal places are a
property of the data rather than of the brand.

### 5. Go to **QA** before delivering.

## The design layer (tokens.json)

Three tiers. A value is written once and referenced everywhere else, so restyling
means editing this file only, never a script and never a `.pptx`.

```
primitive/   the ONLY literal values: color, font, size, space
semantic/    roles: text.*, surface.*, chart.* (categorical, muted, axis, grid, label)
type/        text roles: title, subtitle, section, card_title, body, caption, footer,
             kpi_value, kpi_label, lead -- each {font, size, bold, color, line_height}
layout/      canvas, margin, title_band, gap_in, inset_in, paragraph_space_em,
             and slide_type.<name> -- the CHROME only (background, logo slot,
             title position, footer), never a content arrangement
logo/        path or text wordmark, size
component/   card, kpi, footer_bar, bullet
charts/      _base (incl. grid_width_pt, axis_width_pt) plus one recipe per chart kind
rules/       max_series, single_value_use_kpi
```

**Nothing visual is hardcoded in the scripts.** Not just fonts and colors, but
leading (`type.<role>.line_height`), paragraph rhythm (`layout.paragraph_space_em`),
stroke weights (`charts._base.grid_width_pt` / `axis_width_pt`), the bullet
character and hanging indent (`component.bullet.prefix` / `indent_in`), padding
and gaps. Changing the tokens file
alone must be enough to produce a completely different-looking deck; if you find
yourself wanting to edit a `.py` to change how something *looks*, that value
belongs in the tokens file instead.

Two derived values are computed rather than stored, because storing them would let
two tokens describe one distance and silently drift apart:
`tokens.line_height_in(tk, role)` and `tokens.card_label_pad_in(tk)` (the space a
titled card must leave above its chart, which is card padding + one card_title line
+ the title gap).

Anything in `{braces}` is an alias, resolved against the document root, then
`primitive.*`, then `semantic.*`. Note the singular/plural split: `semantic.chart`
is the chart *palette*, while top-level `charts` holds the styling *recipes*.

### Chart recipes
`charts._base` carries what every chart shares; each kind overrides only what
differs, and `tokens.chart_spec()` merges them. Kinds: `bar`, `bar_stacked`,
`bar_horizontal`, `line`, `area`, `pie`.

The recipes are executable, mapping onto real python-pptx properties
(`value_axis.visible`, `has_major_gridlines`, `major_tick_mark`, `plot.gap_width`,
`plot.overlap`, `data_labels.position/number_format`, `series.smooth`,
`marker.style`, `chart.font`). Two behaviours worth knowing:

- **A bar chart hides its value axis and direct-labels each bar instead.** That is
  the minimalism rule made literal: the labels carry the numbers, so the axis and
  its gridlines are redundant chrome.
- **`max_points_for_labels` is the escape hatch.** Past that many data points
  there are too many bars to label legibly, so `build.py` drops the labels *and
  restores the value axis*, because otherwise the values become unreadable.

### Color rules the layer enforces
- `semantic.chart.categorical` is assigned **in fixed order by series index, never
  cycled**, so a series keeps its color no matter how many others are present.
  Past `rules.max_series`, `build.chart()` raises rather than reusing a hue: fold
  the tail into "Other" or use small multiples.
- `emphasize=i` colors one bar from slot 1 and mutes the rest, for when the story
  is a single bar rather than a comparison of equals.
- A single value is not a chart; `build.chart()` raises and points at
  `build.kpi()`.

When authoring or changing a palette, validate it rather than eyeballing whether
it is colorblind-safe. If the `dataviz` skill is available, its
`scripts/validate_palette.js` checks lightness band, chroma floor, CVD separation
and contrast in one run.

## Workflow B: editing an existing deck substantially
1. Open the file with python-pptx, list slides/shapes to understand current structure before changing anything; never edit blind.
2. Make changes directly on the existing shapes/slides; avoid regenerating slides that don't need to change.
3. If the slide has no free space left and the request needs room (e.g. "add a note above this chart"), resize an existing group in place rather than rebuilding it: shift and shrink only the shapes that anchor the group's far edge (a card, a chart), and shift *without* shrinking any fixed-height shape inside it (a card title is one line regardless of how tall the card around it is). Reducing a title's height by the same amount as the card's drives it negative and python-pptx raises. Verify the edit against shape geometry directly (positions/sizes before vs. after), not only a render: an off-by-one on which shapes anchor vs. shift is easy to miss visually but exact in the numbers.
4. Go to **QA** before delivering. Note `check_design.py` targets decks built from the design layer; on a third-party deck it will legitimately flag its fonts and colors, so read its output as information rather than as a gate.

## Workflow C: one-off tweak
1. Open the file, find the specific slide and shape(s) involved.
2. Make the minimal edit; touch nothing else on the slide.
3. Go to **QA**, scoped to the changed slide's render if the deck is large.

## QA: always, no exceptions
```bash
python scripts/check_file.py deck.pptx
python scripts/check_design.py deck.pptx design/brand.tokens.json
python scripts/render_qa.py deck.pptx --outdir renders
```

- `check_file.py`: zip integrity, required OOXML parts, well-formed XML, python-pptx can open it. Not full ISO/IEC 29500 schema validation, but it catches the real breakage: corrupted files and malformed XML from bad string edits.
- `check_design.py`: conformance against the design layer. Fails on a font or color that isn't in the tokens, a shape off the canvas or with a non-positive width/height, or a chart contradicting its recipe; warns on margin crossings and overlapping peers. This is what makes the tokens binding rather than advisory.
- `render_qa.py`: renders every slide to JPEG. **View every rendered image, not just the first.** Check: no text overflow or clipping, no unintended overlap, nothing off-slide or under the footer, legible labels, colors consistent with the layer.

Fix and re-render if anything is wrong; never ship on "it's probably fine."

## Common pitfalls
- Don't hardcode a font, color, size or coordinate in slide code. If you need one the layer lacks, add it to the tokens file. `check_design.py` will catch you.
- Rule bars and footers often live on the slide **master or layout**, not on individual slides; check `slide.slide_layout` and `slide.slide_layout.slide_master`, not just `slide.shapes`.
- Every run needs its font, size and color set explicitly, which is what `build.text` does. python-pptx always writes a literal typeface onto a run, so a run never inherits the theme's `+mj-lt`/`+mn-lt` and there is no theme-level shortcut to styling text.
- The generated deck keeps the stock theme of `templates/blank.pptx`. That is fine for what this skill produces, since every element is styled from the tokens directly, but it does mean a chart someone later inserts by hand in PowerPoint will use that stock theme rather than the design layer.
- Turning a shadow off needs more than `shadow.inherit = False`. That writes an empty `<a:effectLst/>`, which PowerPoint honours but LibreOffice ignores in favour of the `<p:style><a:effectRef>` shadow, so QA renders disagree with PowerPoint. `build.py` clears `effectRef` too.
- python-pptx exposes no paragraph indent API, so a wrapped bullet line has no hanging indent by default; it falls back to the textbox's left edge instead of aligning under the bullet's own text. `build.bullets()` sets `marL`/`indent` directly in the paragraph XML from `component.bullet.indent_in` to fix this. Verify against a render, not just the XML, when touching this: LibreOffice and PowerPoint can disagree on indent handling the way they do on shadows.
- A single-series chart auto-titles itself with the series name, duplicating the card title above it. `charts._base.chart_title` is false for this reason.
- `XL_DATA_LABEL_POSITION.OUTSIDE_END` is invalid on a stacked plot; `build.py` skips positioning there rather than raising.
- A tokens file's font family is a string, not a guarantee. Verify it resolves to the intended face with `fc-match "<family>"` before trusting a render, especially for weight-specific static faces, where fontconfig's expected name can differ from the font's typographic name. This is per-environment; never bake an assumed-correct family string into a script.
- Fonts not installed in the rendering environment are silently substituted during QA rendering, so the visual check is only approximate; say so rather than implying fidelity.
- Re-render after every edit, even small text changes: line wrapping shifts can create new overlaps.
