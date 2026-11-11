# Issue #1: Insert a chart into an existing slide

Two natural-language requests, two turns. The first builds a starter deck
from scratch; the second edits that deck after the fact, the way a real
follow-up request would arrive; not in the same breath as the first.

## The queries

> 1. Can you make me a quick two-slide deck from data/quarterly_revenue.csv?
>    Just a home slide and then revenue by region as a chart.
>
> 2. Actually, can you add a stacked bar chart of our costs to slide 2 as
>    well? Use data/costs.csv.

## Process

**Step 1** built `starter.pptx`: a home slide, then a "Revenue by Region"
slide whose chart intentionally uses only the left ~55% of the body, the way
a real slide often does, leaving room for exactly the kind of follow-up
request that arrived next.

**Step 2** is the actual subject of this issue: Workflow B, editing a deck
that already has content, not building one from scratch.

- Opened `starter.pptx` directly with python-pptx (not `templates/blank.pptx`)
  and inspected slide 2's existing shapes before touching anything, per
  Workflow B's first rule: never edit blind.
- Computed the occupied region from that inspection rather than assuming it:
  only shapes that both start inside the body's horizontal range and sit
  inside its vertical range count as "occupied content." A first pass without
  the horizontal check mistook the slide's full-canvas background rectangle
  for occupied space (its vertical center falls inside the body purely
  because it spans the whole canvas), which pushed the computed free region
  to a negative width. Silently. `check_file.py` and `check_design.py` both
  passed the resulting deck, because neither checked that a shape's width or
  height was positive. Fixed in `check_design.py`.
- Added a new card + `charts.bar_stacked` chart from `data/costs.csv` in the
  actual free region, styled the same way any chart built from scratch is,
  from the same `design/brand.tokens.json` recipe.
- Verified directly against the shape geometry, not just a visual check: every
  one of the original 9 shapes on slide 2 sits at the exact same position in
  `deck.pptx` as in `starter.pptx`, and slide 1 is untouched entirely. The 3
  new shapes start exactly `layout.gap_in` (0.35in) past where the original
  chart's card ends.
- Ran the mandatory QA: `check_file.py`, `check_design.py` (now catching
  degenerate geometry too), `render_qa.py`.

## A gap this found, fixed in the skill

`check_design.py`'s geometry check tested a shape's edges against the canvas
bounds, but never that its width or height were positive. A box computed from
bad arithmetic, like the negative-width one this exercise produced on the
first pass, could pass QA clean while being invisible or malformed. Added a
dedicated check: `FAIL` on any shape with `w <= 0` or `h <= 0`, before the
existing bounds check runs (a negative width can otherwise look "in bounds"
by accident, since `x + w < x` doesn't trip an upper-bound comparison).

## Result

- `starter.pptx`: the 2-slide deck before the edit
- `deck.pptx`: the same deck after Workflow B added the cost chart
- `renders/before/` and `renders/after/`: rendered JPEGs of both
