# claude-pptx-skills

A Claude Code project skill that generates and edits PowerPoint decks from a
dataset and a natural-language request, using only python-pptx (no
third-party generation tool). Brand identity lives in a versioned design
layer, not in any `.pptx` file, so restyling a deck means editing one JSON
file, not the skill.

## Layout

- `design/brand.tokens.json`: the design layer, the single source of visual truth
- `templates/blank.pptx`: the empty 16:9 deck generation writes into
- `data/`: mock datasets used to drive generated slides
- `.claude/skills/pptx-generation/`: the skill (`SKILL.md` + `scripts/`)
- `examples/`: worked query -> process -> result examples (see below)

## The design layer

Three tiers in `design/brand.tokens.json`, `{alias}` references so a value is
written once:

| Tier | Contents |
|---|---|
| `primitive` | the only literal values: color, font, size, space |
| `semantic` | roles: `text.*`, `surface.*`, `chart.*` (categorical palette, axis, grid) |
| `type` / `layout` / `component` / `charts` | recipes: text roles, slide chrome, cards/KPIs, one styling recipe per chart kind |

Two things worth knowing:

- **Chrome vs. arrangement.** Slide chrome (logo, title position, footer,
  background) lives in `layout.slide_type` and is applied by name. How a
  slide's body is arranged is not a token at all; the agent composes it per
  request with `grid.rows`/`grid.cols`, which split a box into boxes and nest
  freely.
- **Chart recipes are executable, not advisory.** Each key maps to a real
  python-pptx property. A bar chart hides its value axis and direct-labels
  each bar instead; `max_points_for_labels` restores the axis once there are
  too many bars to label legibly.

Scripts: `tokens.py` (resolves aliases), `build.py` (builds slides from the
layer), `grid.py` (splits boxes), `check_design.py` (fails QA on anything
off-token).

## The skill

One skill, **pptx-generation**. It classifies a request into one of three
workflows:

- **A, new deck or new slides**: `build.new_slide()` for chrome, `grid.rows`/
  `grid.cols` to compose the arrangement, `build.py` helpers for every font,
  color and size, all read from the design layer.
- **B, editing an existing deck**: open the file as-is, edit shapes directly,
  don't regenerate from scratch.
- **C, a one-off tweak**: open the file, make the minimal edit.

Every workflow ends in mandatory QA:

- `check_file.py`: zip integrity, required OOXML parts, well-formed XML
- `check_design.py`: conformance against the design layer (fonts, colors,
  geometry, chart recipes)
- `render_qa.py`: renders every slide to JPEG for visual inspection

## Examples

Each is a worked natural-language query, the process the agent followed, and
the resulting deck, kept in the repo rather than gitignored.

- [`issue-4-prompt-to-deck`](examples/issue-4-prompt-to-deck): one prompt + several datasets -> a 4-slide deck, agent-decided structure
- [`issue-2-key-insights`](examples/issue-2-key-insights): one dataset -> a slide of 5 computed insights, no numbers supplied
- [`issue-1-insert-chart`](examples/issue-1-insert-chart): opening an existing deck and inserting a new chart into a slide that already has content
- [`issue-3-resize-chart`](examples/issue-3-resize-chart): a slide with no free space, resizing an existing chart in place to add a text note

## Prerequisites

```bash
sudo apt-get install -y libreoffice poppler-utils
python3 -m venv .venv
.venv/bin/pip install python-pptx
```

Run any script with `.venv/bin/python .claude/skills/pptx-generation/scripts/<script>.py ...`.

## Status

Design layer and skill validated end-to-end against four scenarios; see `examples/`.
