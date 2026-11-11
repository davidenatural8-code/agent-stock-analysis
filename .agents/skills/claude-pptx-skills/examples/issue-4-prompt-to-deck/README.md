# Issue #4: Prompt-to-deck

One natural-language request, the raw files in `data/`, and the design layer
in `design/brand.tokens.json` produced `deck.pptx`. Nothing below was
pre-computed before the request was made: every number on every slide is
derived from a CSV at generation time.

## The query

> Hey, can you put together a short FY25 business review deck from the data
> in `data/`? Start with a home slide, then a performance summary with our
> key numbers and revenue by region, a highlights slide with the big
> takeaways plus how our active users and revenue mix moved this year, and
> finish with an operational dashboard covering bookings, costs, headcount
> and customer health. Keep it on-brand and make sure the charts look clean,
> and don't get into the weeds, just show me what actually matters.

## Process

- Classified as Workflow A (new deck) per `SKILL.md` Step 0.
- Loaded the design layer (`design/brand.tokens.json`) for every font, color
  and chart recipe: nothing here is styled ad hoc.
- Read the raw rows from `quarterly_revenue.csv`, `monthly_active_users.csv`,
  `revenue_mix.csv`, `bookings.csv`, `costs.csv`, `headcount.csv` and
  `customer_health.csv`.
- Decided on its own: four slides total, which chart kind fits each section
  (bar, line, pie, area, stacked bar), the three headline KPIs, and which
  points were actually worth calling out in the "What changed this year" text
  and the three stat callouts on slide 3, all computed from the raw rows,
  not supplied in the request:
  - FY25 revenue and YoY growth (summed and compared against FY24)
  - APAC's YoY growth specifically (fastest of the three regions, off the
    smallest base)
  - Services' share of revenue, Q1 vs Q4 (a real mix shift, not a single
    number)
  - Enterprise churn, Q1 vs Q4
- Composed each slide's layout with `grid.rows`/`grid.cols` (weighted splits,
  chosen per slide, no preset layout involved), used `build.new_slide` for
  chrome (logo, title placement, footer) and `build.card`/`build.chart`/
  `build.kpi` for content.
- Ran the mandatory QA: `check_file.py` (structural validity), `check_design.py`
  (every font, color and chart recipe checked against the design layer, zero
  violations), `render_qa.py` (visual check, see `renders/`).

## Result

- `deck.pptx`: 4 slides
- `renders/slide-1.jpg` … `slide-4.jpg`

Numbers that ended up on the slides, all computed rather than looked up:
FY25 revenue **$396M** (+34% YoY), APAC **+90%** YoY, services mix
**18% → 23%**, Enterprise churn **3.4% → 2.7%**, cumulative bookings
**$58M**.

## Note on other issues

This deck also demonstrates capabilities the other open issues test directly,
without being built for them:

- **Issue #2** (insights from raw data): the "What changed this year" text and
  the three stat callouts on slide 3 are all computed from raw rows, not
  handed numbers.
- **Issue #3** (chart-with-legend, on-brand): the "Revenue by region" chart on
  slide 2 uses `semantic.chart.categorical` colors and a positioned legend
  with no styling instructions given.

Left both open rather than closing them here: each calls for its own
dedicated, single-purpose test.
