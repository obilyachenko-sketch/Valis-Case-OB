# Tax-form chaser — run report

Input `support_tickets_q1_2026.csv`: 140 rows, 0 quarantined · **36 tax-form tickets** from 36 creators · period 2026-01-02 → 2026-03-31 · tracker as of **2026-03-31**

## Before → after (per quarter)
| | Before (measured) | After (modelled) | Change |
|---|---:|---:|---:|
| Handle time | 25.9 h | 10.0 h | **−15.9 h (−61.5%)** |
| Per week | 1.99 h | 0.77 h | −1.23 h |
| Manual chase threads | 36 | 7.2 hand-offs (expected) | −28.8 |
| Time cost per year @ $20/h | $2,073 | $798 | **−$1,275** |

**Before** = sum of `Handle_Minutes` on the 36 tax-form rows (measured). **After** = for each request, 10 min to check the returned form, or the original minutes if it's handed to a person (20% assumed). Loaded $/h: `pnl_q1_2026.csv:L7` ÷ `headcount_roster.csv:L18` × 4 ÷ 2,080 h.

**Break-even:** an e-sign/tax-form service pays for itself on time alone if it costs less than **$1,275/year** — the time saved, not the full $2,073, because checking returned forms and hand-offs still cost time. People called these services 'cheap' (`slack_export.md:L204`); no price in the data.

## By month
| Month | Tickets | Before h | After h |
|---|---:|---:|---:|
| 2026-01 | 12 | 8.8 | 3.4 |
| 2026-02 | 10 | 7.8 | 2.9 |
| 2026-03 | 14 | 9.3 | 3.7 |

## Sensitivity — hours saved per quarter
| Hand-off rate ↓ · check minutes → | 5 min | 10 min | 15 min |
|---|---:|---:|---:|
| 10% | 20.6 | 17.9 | 15.2 |
| 20% | 18.3 | 15.9 | 13.5 |
| 30% | 16.0 | 13.9 | 11.8 |
| 50% | 11.5 | 10.0 | 8.5 |

## What the chaser did (replay of the period, dry-run)
144 messages scheduled: ESIGN_REQUEST 36, HANDOFF_TO_PERSON 36, REMINDER_1 36, REMINDER_2 36. Inside the period: 36 e-sign requests, and — if no form were ever returned (worst case) — up to 67 reminders and 29 hand-offs; reminders stop as soon as a form comes back, so the expected hand-offs are ~7 at the assumed 20%. Busiest day: 2026-01-16. Day-by-day log: `replay_by_day.csv`; every message: `outbox.jsonl`; state per request: `tracker.csv`.

## Chase list for 2026-03-31 — steps due today if the form isn't back yet
- TF-TCK-1117 — REMINDER_2 → creator_nightjar

## Data quality
- No rows quarantined.
- TCK-1013 (line 14): blank Assigned_To — kept; effort is still logged
- No country field in the log, so the chaser can't pre-pick W-9 vs W-8BEN; the creator selects in the e-sign flow.
- No 'form returned' date in the log, so return rates can't be measured yet; the spec makes logging it step 1.
