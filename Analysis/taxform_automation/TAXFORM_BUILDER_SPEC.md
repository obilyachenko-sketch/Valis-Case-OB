# Builder spec — Tax-form chaser (W-9 / W-8), v1

**Owner:** Liam Doyle (Ops) · **Sponsor:** Marcus Lindqvist (COO) · **Tool decision:** Elena Novak (People) · **Prototype (runs today, dry-run):** `Analysis/automation/taxform_chaser.py`

## Why this workflow
- **Biggest measured support category:** 36 tickets, **1,555 min (25.9 h) in Q1**, average 43 min, every ticket from a different creator (`support_tickets_q1_2026.csv`).
- **Manual chasing, flagged twice by Ops:** "constant follow-up" (`slack_export.md` L171); "Manual every time. Anyone got a tool rec?" (L201).
- **People has already pointed to the fix:** "e-sign + tax form services. Cheap" (L204).
- **Why not reconciliation:** its 3 inputs aren't available; see `Analysis/automation/RECON_SCOPE.md`.

## Result on the real data (Q1, 140 rows)
| | Before (measured) | After (modelled) |
|---|---:|---:|
| Handle time per quarter | **25.9 h** | **10.0 h (−15.9 h, −61.5%)** |
| Manual chase threads | 36 | ~7 hand-offs |
| Time cost per year @ $20/h | $2,073 | $798 |

The service **breaks even below $1,275/year**. Sensitivity: **8.5–20.6 h saved per quarter** across hand-off rates of 10–50% and 5–15 minutes to check each returned form (`Analysis/output/taxform/report.md`).

## Scope
| In (v1) | Out (v1) |
|---|---|
| Every ticket whose `Category` matches `^Tax form` → one form request | Thumbnails, payouts, login/access/takedown tickets |
| E-sign request on the ticket date; reminders on day 3 and 7; hand-off to a person on day 14 if the form isn't back | Choosing W-9 vs W-8 for the creator (no country in the data; the creator selects) |
| Reminders stop the moment a form is returned | Tax advice; validating TIN numbers |
| Tracker per request, daily chase list for Ops, full audit log | Storing completed forms (stays in the e-sign provider) |
| Before→after report on every run | Live sending before acceptance passes in staging |

## Data contract (input) — `support_tickets_q1_2026.csv`, columns exactly as delivered
| Column | Rule | On violation |
|---|---|---|
| `Ticket_ID` | `TCK-<digits>`, unique | quarantine |
| `Date` | ISO `YYYY-MM-DD`, valid date; this is day 0 of the schedule | quarantine (`bad Date`) |
| `Category` | non-blank; `^Tax form` selects the row | blank → quarantine; anything else → ignored |
| `Submitted_By` | creator handle; the message recipient | — |
| `Assigned_To` | may be blank (1 tax row in Q1: TCK-1013) | hand-off defaults to "Ops Support" |
| `Handle_Minutes` | integer 1–480 | quarantine |
| `Status` | `Open` / `Closed` | quarantine |

UTF-8 or UTF-16 input is accepted. A missing column fails the whole run. **New field the builder must add:** `form_returned_date`, written back by the e-sign webhook. It replaces the two modelled assumptions with measured ones.

**Outputs:** `tracker.csv` (one row per request, with its state) · `outbox.jsonl` (every message: request_id, type, to, date, template, condition) · `chase_list_<date>.csv` · `replay_by_day.csv` · `quarantine.csv` · `summary.json` · `report.md`.

## Build steps
1. Swap the dry-run outbox for the chosen e-sign provider's API (W-9 and W-8BEN templates); the outbox stays as the audit log.
2. Webhook on completion → set `form_returned_date` → cancel pending reminders.
3. Run daily; post `chase_list_<today>.csv` to Ops (the hand-offs only).
4. After 4 weeks, replace `escalation_rate` and `residual_minutes` in `taxform_config.json` with measured values.

## Acceptance test — "answer-complete" (`python -m unittest discover -s Analysis/tests -v`)
1. **Every tax-form row becomes exactly one request:** 36 in Q1; every input row is processed, ignored as non-tax, or quarantined with a reason.
2. **`before_minutes` equals the raw sum** of `Handle_Minutes` for those rows (**1,555**).
3. **Each request has exactly** 1 e-sign request, 2 reminders and 1 hand-off, on the configured days (TCK-1002: reminders 2026-01-05 and 01-09, hand-off 2026-01-16).
4. **The replay covers every day** of the period, and its e-sign total equals the request count.
5. **Idempotent:** two runs on the same input give byte-identical outputs.
6. **Dirty input is handled:** a UTF-16 file with a duplicate ID, an invalid date and non-numeric minutes quarantines those 3 rows and processes the rest. A file with no tax rows fails loudly.
7. **A new quarter's file runs unchanged** (Q2 test).

**Done (v1) =** tests green, plus 4 weeks live with measured hand-offs ≤ 30% and Ops tax-form time ≤ 50% of the Q1 baseline (≤ 1.0 h/week vs 1.99).

## Open items
- **Vendor and price.** People: "cheap" (L204), with no figure in the data. It must cost < $1,275 a year to pay back on time alone.
- **Does tax-form volume really peak?** "Tax form season again" in June (L201) suggests it recurs, so check against Q2 tickets.
