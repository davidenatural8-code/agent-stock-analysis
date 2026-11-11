# Issue #3: Resize an existing chart to make room

Two natural-language requests, two turns, the same pattern as issue #1: build
a starter deck, then come back and edit it after the fact. This one is the
harder edit, though: the starter slide has no free space anywhere, so
satisfying the second request means resizing something that's already there,
not placing new content in a gap.

## The queries

> 1. Can you build me a two-chart slide from data/quarterly_revenue.csv and
>    data/monthly_active_users.csv? Revenue by region on the left, monthly
>    active users on the right, side by side, using the full slide.
>
> 2. Can you add a short text note above the left chart, no box or border
>    around it, just plain text? Something like "Europe led every quarter."
>    Shrink the chart if you need to, but don't touch the other one.

## Process

**Step 1** built `starter.pptx`: one slide, two charts, each filling its full
column height with `grid.cols(tk, body, n=2)`, no space reserved anywhere for
anything else.

**Step 2** is the actual subject of this issue:

- Opened `starter.pptx` (not `templates/blank.pptx`) and inspected its
  shapes, classifying them into the left column and the right column by
  position, the same body-vs-chrome filter issue #1 used (only shapes that
  start inside the body's horizontal range and sit inside its vertical range
  count as content, excluding the slide's background/title/footer).
- Computed the space the new note needs from `tokens.line_height_in(tk,
  "caption")` plus a token gap on each side, not a guessed constant.
- Shrank the left column's card and chart in place, in the correct sense:
  pushed their top down and reduced their height by the freed amount, so
  their bottom edge stays exactly where the right chart's bottom edge is.
  The card's title textbox only got pushed down, its own height left alone,
  since it's a single fixed-height line, not something that scales with the
  card around it.
- Added the plain text note (`build.text`, no card, no fill) in the freed
  strip, sized to the box that computation produced.
- Left every shape in the right column untouched.
- Verified directly against shape geometry, not just a render: the right
  column's 3 shapes are at the exact same position in `deck.pptx` as in
  `starter.pptx`; the left column's 3 shapes are shifted down and shrunk by
  exactly the freed amount, with both columns' bottoms still aligned.
- Ran the mandatory QA: `check_file.py`, `check_design.py`, `render_qa.py`.

## A mistake this exercise made, and what it means for the skill

The first attempt shrank every shape in the left column by the same amount,
including the card's title textbox, and crashed: python-pptx refused a
negative height. The title textbox is a single line positioned just inside
the card, not a shape whose height should track the card's height. Fixed by
only shrinking the shapes that actually anchor the column's bottom edge (the
card, the chart) and only repositioning the title.

No token or script needed to change for this: `tokens.line_height_in`,
`layout.gap_in`, and plain python-pptx shape geometry were already enough.
The gap was in reasoning about which shapes should shrink versus which
should only move, not in a missing capability, so this is now documented as
guidance in `SKILL.md`'s Workflow B instead of a code change.

## Result

- `starter.pptx`: the 1-slide deck before the edit, both charts full height
- `deck.pptx`: the same deck after the note was added and the left chart resized
- `renders/before/` and `renders/after/`: rendered JPEGs of both
