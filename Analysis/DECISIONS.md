# Decisions

| ID | Decision | Date | Record |
|---|---|---|---|
| D1 | Workflow to automate: **tax-form chasing (W-9 / W-8)**; reconciliation dismissed (data missing) | 2026-10-28 | [taxform_automation/DECISIONS.md](taxform_automation/DECISIONS.md) |
| D2 | Value number for the CFO: **$41,600 / year, support hire avoided** | 2026-10-28 | below |

## D2 — Value number: $41,600 / year, support hire avoided
**Date:** 2026-10-28 · **Decided by:** Olga Bilyachenko · **Status:** Final for the summary deck (Q3 slide) · **Confidence:** Medium

**The number.** Ops asked for a full-time creator-support hire on a felt "easily 40 hrs/week" (`slack_export.md` L176, L188). The Q1 ticket log measures **5.4 h/week (0.14 FTE)**, and the current team already absorbs it. Not opening the req avoids one loaded FTE: $3,120,000 ÷ 300 FTE × 4 = **$41,600 / year** (`pnl_q1_2026.csv` L7, `headcount_roster.csv` L18). It's **cost avoidance**, booked as "req not opened", not a cut to existing spend.

| | Value | Source |
|---|---|---|
| Claimed load | 40 h/week = 1.0 FTE | slack L176, L188 |
| Measured load | 140 tickets, 4,230 min = 70.5 h/qtr = 5.42 h/week = 0.14 FTE | `support_tickets_q1_2026.csv` L2–L141 |
| Loaded cost per FTE | $41,600 / year | P&L L7 ÷ roster L18 × 4 |
| **Value** | **$41,600 / year** | (1 FTE requested − 0 needed) × cost |
| Floor (worst case) | **$20,129 / year**: if the May spike (47 thumbnail swaps in one week, slack L193) were typical, 0.52 FTE would be needed | `output/Value number raw data.xlsx` → Summary B32 |

**Why this number** (alternatives ranked lower, see the workbook's *Alternatives* tab):
- **Amplitude duplicate, $30,000/yr:** can't tell a cash leak from a booking error without the invoice.
- **Reconciliation time, ~$5,760/yr:** self-reported, and its data is missing.
- **Automation hours, ~$2,400/yr:** modelled and small.

**Consistency with D1.** The worksheet's "with automation" scenario ($30,991) assumes thumbnail swaps are also automated. They aren't part of the selected automation, so the decision quotes the **manual floor ($20,129)**. With tax-form automation only, the worst case is ~0.49 FTE (~$21,400 / year), so the floor stands.

**What could not be verified:**
- Q2 ticket volume, the biggest risk;
- whether a formal support req exists;
- effort spent outside the ticketing tool;
- how `Handle_Minutes` is recorded;
- the role-specific loaded cost.

**Revisit when:** Q2 support tickets arrive from Ben Okoro (slack L185). The same scripts re-run unchanged and either confirm $41,600 or move it toward the floor.

**Artefacts:** [VALUE_NUMBER.md](VALUE_NUMBER.md) · [Value number raw data.xlsx](output/Value%20number%20raw%20data.xlsx) · [value_number_chart.png](output/value_number_chart.png) (Q3 slide chart)
