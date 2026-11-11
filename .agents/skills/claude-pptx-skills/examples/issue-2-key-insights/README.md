# Issue #2: Key insights from raw data

One natural-language request and the raw rows in `data/customer_health.csv`
produced this one-slide deck. No number below was supplied in the request:
every figure, and every comparison between segments, was computed from the
CSV at generation time.

## The query

> Can you add a slide summarizing the key insights from
> data/customer_health.csv? Just give me like 5 bullet points of what
> actually matters, nothing fancy, one slide is enough.

## Process

- Loaded the design layer (`design/brand.tokens.json`) and read the raw rows
  from `customer_health.csv`: segment x quarter, NPS and churn, FY25 Q1-Q4.
- Computed, per segment, the Q1-to-Q4 change in NPS and churn, both in
  absolute points and in relative percent, then ranked segments against each
  other rather than reporting each one in isolation. That comparison is where
  the real insights are: every segment gained exactly 3 NPS points, which
  reads as a flat, uninteresting fact until it's compared in relative terms
  (SMB's 3-point gain is worth more, proportionally, than Enterprise's).
- Picked 5 points that survive that comparison, not one per data row (the
  file has 12 rows: 3 segments x 4 quarters):
  1. NPS rose in every segment, all gaining the same 3 points
  2. but SMB's relative gain (+8.6%) was the largest of the three
  3. churn fell everywhere too, led by Mid-Market's relative improvement
  4. Enterprise stayed both the highest-NPS and lowest-churn segment all year
  5. despite improving fastest, SMB still churns highest of the three in Q4
- Rendered the 5 points as a plain bulleted text box (`build.bullets`) sized
  from a new `type.lead` role, no card. A card wasn't warranted for a single
  block of text on an otherwise empty slide, and skipping one doesn't bypass
  the design layer: `build.bullets`/`build.text` read `type.<role>` for font,
  size and color regardless of what shape they're placed in or on.
- Ran the mandatory QA: `check_file.py`, `check_design.py` (zero violations),
  `render_qa.py` (see `renders/`).

## A design-layer gap this surfaced

The first pass used the existing `type.body` role (11pt) inside a card, which
looked cramped against how much empty space a single 5-bullet slide actually
has. Rather than hardcode a bigger font size in the generation script, added
`primitive.size.xl` (18) and a new `type.lead` role to `design/brand.tokens.json`
for exactly this case: a spacious, primary-colored block of text that isn't a
card title or a caption. This is a reusable addition to the type scale, not a
one-off fix.

Separately, rendering that larger text exposed a real bug in
`build.bullets()`: a wrapped bullet's second line fell back to the textbox's
left edge instead of aligning under the bullet's own text, because python-pptx
exposes no paragraph indent API and the original implementation never set one
in the underlying XML. Fixed in `build.py` by setting `marL`/`indent` directly
on each bullet paragraph, with the indent width itself as a token
(`component.bullet.indent_in`). Verified against the rendered JPEG, not just
the XML: LibreOffice honors the hanging indent correctly.

## Result

- `deck.pptx`: 1 slide
- `renders/slide-1.jpg`
