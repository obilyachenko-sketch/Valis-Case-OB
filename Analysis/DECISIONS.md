# Decision record

## D1 — Workflow to automate: tax-form chasing (W-9 / W-8)
**Date:** 2026-10-28 · **Decided by:** Olga Bilyachenko (tested locally before confirming) · **Status:** Selected, built and running (`automation/taxform_chaser.py`)

### Candidates considered
Source: `output/Time waste raw data.xlsx` → Workflows (hours, criticality reasons and source lines). Criticality = 5 dimensions × 1–3 (money exposure, trust in the numbers, deadline pressure, key-person risk, growth), max 15.

| # | Process | Hours / quarter | Criticality (/15) | Decision | Rationale |
|---|---|---:|---:|---|---|
| 1 | Brand-deal revenue reconciliation (CRM ↔ invoicing ↔ payouts) | ~72 (claimed; 45–84) | 15 | **Dismissed: data missing** | Highest criticality (80% of revenue, board numbers, one person, every close). But none of the 3 inputs (CRM export, invoicing sheet, payout tracker) is in the data, so it can't run end to end. Scoped for later: `automation/RECON_SCOPE.md` |
| 2 | **Tax-form chasing (W-9 / W-8)** | **25.9 (measured)** | 9 | **Selected** | Largest measured support item (36 tickets, 1,555 min); fixed playbook; Ops flagged it twice (slack L171, L201); People pointed to e-sign tools (L204); runs on the real ticket data |
| 3 | Thumbnail re-uploads | 22.8 (measured) | 6 | Not selected | Low value per ticket (slack L196); self-serve needs a CMS/engineering build that isn't scoped |
| 4 | Payout questions | 14.6 (measured) | 8 | Not selected | Answering needs the payout tracker — missing, the same gap as #1 |
| 5 | Other support (login, access, takedowns) | 7.2 (measured) | 5 | Not selected | Security / legal judgment; small |
| 6 | "Active creators" number (1,210 vs 1,840) | not quantified | 11 | Not automation | A definition decision, not a workflow (slack L59); owners Priya + Ben |
| 7 | Post-production bottleneck | not quantified | 9 | Not selected | No throughput data |
| 8 | Vendor / SaaS hygiene | not quantified | 9 | Not selected | No invoices in the data; small |

### Result of the selected automation (Q1 data, 140 rows)
- **Hours:** 25.9 → 10.0 a quarter (−61.5%). Before is measured; after is modelled (10 min to check a form, 20% handed to a person).
- **Workload:** 36 manual chase threads → ~7 hand-offs.
- **Cadence:** e-sign request on day 0, reminders on day 3 and 7, hand-off to a person on day 14 → 144 messages.
- **Break-even:** the tool must cost less than $1,275 a year to pay back on time alone.
- **Tests:** 25 acceptance tests pass; the spec is `automation/TAXFORM_BUILDER_SPEC.md`.

### Revisit
Reopen #1 (reconciliation) as soon as Finance shares April/May exports of the 3 sources plus Maya's written-up steps (`finance_review_2026-05-28.md` L36).
