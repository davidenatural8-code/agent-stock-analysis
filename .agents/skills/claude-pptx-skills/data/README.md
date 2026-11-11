# Mock data

FY24-FY25 performance data for a fictional B2B SaaS company. Deliberately kept
raw (one row per quarter/month x dimension) rather than pre-aggregated, so
generating a "key insights" slide requires actually computing a trend, a
mix-shift, or an outlier from the rows, not just formatting numbers already
handed to it.

- `quarterly_revenue.csv`: quarter, region (Europe/Americas/APAC), revenue_musd.
  Two fiscal years, so YoY growth is computable per region. APAC is smallest in
  absolute terms but grows fastest in relative terms.
- `monthly_active_users.csv`: month, segment (Enterprise/SMB), mau_k. Twelve
  months of FY25. Both segments dip for one month before resuming growth
  (Enterprise in October, SMB in November): a real anomaly to find, not a
  fabricated one.
- `revenue_mix.csv`: quarter, category (Subscriptions/Services/Licences/Other),
  revenue_musd. Services' share of total revenue grows every quarter relative
  to the others.
- `headcount.csv`: quarter, function (Engineering/Sales/Support/G&A),
  headcount. Steady growth, heaviest in Engineering.
- `customer_health.csv`: quarter, segment (Enterprise/Mid-Market/SMB), nps,
  churn_pct. NPS rises and churn falls in every segment, largest gains in SMB.
- `costs.csv`: quarter, cost_type (Fixed/Variable), amount_musd. Variable cost
  grows faster than fixed cost over the year.
- `bookings.csv`: quarter, new_bookings_musd. New bookings per quarter, not
  cumulative: a cumulative-bookings chart requires summing the rows first.

Numbers are consistent across files where they overlap (e.g. `headcount.csv`'s
FY25-Q4 row matches the FY25-Q4 figures used in the design-layer demo deck),
so combining files into one slide or deck doesn't produce contradictions.
