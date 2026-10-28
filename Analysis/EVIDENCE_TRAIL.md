# Evidence Trail — CEO questions

Every claim maps to a file and line number (line numbers from `cat -n` on the files at repo root; `CEO_QUESTIONS.md` read after UTF-16→UTF-8 conversion). Status: **preliminary** — answers are drafted in the next step.

---

## Q1. "What did we actually spend on SaaS tools last quarter?"

| # | Evidence | Source |
|---|---|---|
| 1 | 15 Software & SaaS line items, Q1 2026 | `pnl_q1_2026.csv` L9–L23 |
| 2 | Subtotal as listed: $81,000 ("as-listed sum") | `pnl_q1_2026.csv` L24 |
| 3 | Recomputed sum of L9–L23 = $81,000 (ties) | build log JC-04 |
| 4 | Amplitude $7,500 + Amplitude Analytics $7,500 — suspected double-count, unconfirmed | `pnl_q1_2026.csv` L12–13; `slack_export.md` L147, L150, L153 |
| 5 | CFO: SaaS finalized at $81k; AWS (~$38k) is Infrastructure, don't fold in | `slack_export.md` L144 |
| 6 | Salesforce Q1 $12,000; $60k/yr renewal closed 2026-05-14 (Q2) | `pnl_q1_2026.csv` L9; `slack_export.md` L119; `meeting_notes/finance_review_2026-05-28.md` L23 |
| 7 | Finance note claims posted Salesforce figure looks *higher* than $60k/yr implies — arithmetic says lower ($12k vs $15k/qtr) | `meeting_notes/finance_review_2026-05-28.md` L23 |
| 8 | EUR-billed tools must be FX-normalized; only visible EUR line is Cloudflare (infra) | `meeting_notes/finance_review_2026-05-28.md` L25; `pnl_q1_2026.csv` L26–27 |

**Working answer:** $81,000 as booked; **$73,500** if the Amplitude duplicate is confirmed. Range $73.5k–$81k.
**Confidence (draft):** High that $81k is what's booked; medium that $73.5k is the true spend (pending Amplitude invoice).
**Can't verify:** Amplitude invoice; whether any SaaS line is EUR un-normalized; whether SaaS is expensed elsewhere (e.g., team cards).

---

## Q2. "Did we decide to hire in Sales or freeze — current state, and who owns it?"

| # | Evidence | Source |
|---|---|---|
| 1 | Roster snapshot 2026-05-01: REQ-114 Sales AE `APPROVED`, start 2026-07-15, HM Tomás Reyes | `headcount_roster.csv` L2, L22 |
| 2 | Apr 21: Tomás pushes REQ-114; Marcus says wait; Dana "Park it" | `slack_export.md` L17, L20, L26 |
| 3 | **Jun 10: Dana — FREEZE all new Sales headcount; REQ-114 included; Priya holds the line** | `slack_export.md` L67 |
| 4 | Priya: REQ-114 paused, not killed | `slack_export.md` L70 |
| 5 | Tomás objection on record | `slack_export.md` L73 |
| 6 | Dana: "current state is frozen… I'm making the call, Priya enforces" | `slack_export.md` L79 |
| 7 | Leadership minute: DECISION, owner Dana, enforcer Priya, roster superseded, revisit at July sync | `meeting_notes/leadership_sync_2026-06-11.md` L16–L19 |
| 8 | Scope: net-new Sales only; backfills case-by-case (Priya + Tomás) | `meeting_notes/leadership_sync_2026-06-11.md` L17 |
| 9 | Open loose end: late-stage REQ-114 candidate; Greenhouse pause via Marcus→Elena | `meeting_notes/leadership_sync_2026-06-11.md` L20–21, L42–43 |
| 10 | People confirms freeze, roster stale, Sales-only | `slack_export.md` L230, L236, L244 |

**Working answer:** **Frozen.** Decision owner: Dana Whitfield (CEO). Enforcer: Priya Raman (CFO). REQ-114 paused (not cancelled). Revisit: July leadership sync, on pipeline-coverage trigger. The May 1 roster's "APPROVED" is stale.
**Confidence (draft):** High — four independent sources agree.
**Can't verify:** whether the July revisit happened (bundle ends 2026-06-18); outcome of the late-stage candidate; whether Greenhouse was actually paused.

---

## Workflow question — "Where are we wasting the most time?"

| Candidate | Measured / claimed time | Source | Quality |
|---|---|---|---|
| Brand-deal 3-way revenue recon (CRM ↔ invoicing ↔ payouts) | ~3 days/month (~24 h/month) | `slack_export.md` L108, L158; `finance_review` L11–13; `leadership_sync` L35 | Claimed, consistent across 4 sources; source systems **not in bundle** |
| Creator support (all categories) | **70.5 h/quarter ≈ 5.4 h/week** measured vs "40 h/week" claimed | `support_tickets_q1_2026.csv` (140 rows); `slack_export.md` L176 | Measured |
| – Tax forms W-9/W-8 | 36 tickets, 25.9 h, avg 43 min | tickets | Measured |
| – Thumbnail re-uploads | 63 tickets, 22.8 h, avg 22 min | tickets; `slack_export.md` L165, L193 | Measured |
| – Payout questions | 18 tickets, 14.6 h, avg 49 min | tickets | Measured |
| Post-production bottleneck | not quantified | `slack_export.md` L34, L250 | Claimed only |

**Draft read:** On the evidence, the recon (~24 h/month) outweighs all logged support (~23 h/month). Within support, tax forms cost the most time, not the thumbnail swaps that get the most noise.
