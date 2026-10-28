# Builder spec — Creator-support autopilot (v1)

**Owner:** Liam Doyle (Ops) · **Sponsor:** Marcus Lindqvist (COO) · **Working prototype:** `Analysis/automation/support_autopilot.py` (runs today, dry-run)

## Problem (measured, not felt)
Q1 2026 creator support = **140 tickets, 4,230 handle-minutes (70.5 h)** in `support_tickets_q1_2026.csv`. Two repetitive categories make up **69% of that time**: tax forms W-9/W-8 (36 tickets, 25.9 h, avg 43 min) and thumbnail re-uploads (63 tickets, 22.8 h, avg 22 min). Both follow a fixed playbook: send a link, chase, verify. Ops flagged both (`slack_export.md:L165`, `L171`, `L193`, `L201`).

## Scope
| In (v1) | Out (v1) — and why |
|---|---|
| Route `Tax form (W-9/W-8)` → e-sign request + reminders at day 3/7/14 + escalate at day 21 | `Payout question` — needs the payout tracker (not available; same gap blocks the brand-deal recon) |
| Route `Thumbnail re-upload` → self-serve replace link, human fallback on reply | `Login issue`, `Account access` — security; keep human |
| Validate every row, quarantine bad ones with a reason | `Content takedown` — legal/brand judgment |
| Before→after report on every run | Sending real messages before the acceptance test passes in staging |

## Data contract (input)
File: CSV, UTF-8 or UTF-16 (BOM detected), one row per ticket. Columns are exactly those in `support_tickets_q1_2026.csv`:

| Column | Type / rule | On violation |
|---|---|---|
| `Ticket_ID` | `TCK-<digits>`, unique per file | quarantine (`bad Ticket_ID` / `duplicate Ticket_ID`) |
| `Date` | ISO `YYYY-MM-DD`, valid calendar date | quarantine (`bad Date`) |
| `Category` | non-blank; routing key into `playbooks.json` | blank → quarantine; unknown → route `HUMAN` |
| `Submitted_By` | creator handle (`creator_*`) | used as recipient; not validated beyond non-blank |
| `Assigned_To` | free text, may be blank | blank → warning only (4 such rows in Q1: TCK-1013/1038/1068/1100) |
| `Handle_Minutes` | integer 1–480 | quarantine (`non-numeric` / `out of 1-480`) |
| `Status` | `Open` or `Closed` | quarantine (`unknown Status`) |
A missing column fails the whole run (no partial output).

**Outputs:** `ticket_decisions.csv` (one row per valid ticket: route, actions, before_min, after_min, source_line) · `outbox.jsonl` (one action per line: `ticket, type, to, send_on, template, condition`) · `quarantine.csv` (row + `errors`) · `summary.json` · `report.md`.

## Build steps for the remote builder
1. Swap the dry-run outbox for real calls: CMS thumbnail-replace endpoint (signed, single-use link per ticket) and an e-sign provider (W-9 / W-8BEN templates). Keep `outbox.jsonl` as the audit log.
2. Reply-to-human: any creator reply on a deflected ticket reopens it to Ops Support with the original context.
3. Reminder jobs check "form returned?" before sending; idempotent on `ticket + type + send_on`.
4. Start logging `deflected` / `fell_back` / `residual_minutes` per ticket. **This replaces the two modelled assumptions below with measured numbers after 4 weeks.**

## Assumptions to replace with measurement
`fallback_rate` 20%, thumbnail residual 5 min, tax-form residual 10 min (`playbooks.json`). Sensitivity: saved hours/quarter range **13.1–33.7 h** across 10–50% fallback and 1×–2× residual (see `report.md`).

## Acceptance test — "answer-complete"
Run `python -m unittest discover -s Analysis/tests -v`. It passes only if:
1. `processed + quarantined == input rows`, and every `Ticket_ID` appears exactly once in `ticket_decisions.csv`.
2. `before_minutes` equals the raw sum of `Handle_Minutes` (**4,230** on the Q1 file).
3. Every deflected ticket has ≥1 outbox action and no `HUMAN` ticket has any. Out-of-scope rows keep `after_min == before_min`.
4. A dirty UTF-16 file with a duplicate ID, invalid date (`2026-13-02`), negative minutes and blank category quarantines exactly those 4 rows with the right reasons and processes the rest. An unknown category routes to `HUMAN`.
5. A file missing a required column fails loudly.
6. `report.md` shows before, after, assumptions and the sensitivity table.

**Done (v1) =** tests green + 4 weeks live with measured fallback ≤ 30% and Ops handle time on the two categories down ≥ 40% vs. the Q1 baseline (48.7 h/qtr ≈ 3.7 h/wk).

## Result on the Q1 data (today's run)
Before **70.5 h** → after **40.6 h** per quarter (**−29.9 h, −42.5%**). Tickets needing a person: 140 → ~61. 243 actions generated for 99 tickets.
