# Ask-with-sources — CEO questions

_Generated 2026-10-28 17:19 by `Analysis/ask.py` from the raw files in `valis-case-ob/`. Citations are `file:Lline`._

**Confidence scale used**
- **High** — read directly from a primary record *and* corroborated by an independent source; no open conflict.
- **Medium** — primary record exists, but a documented open issue could move the number.
- **Low** — single uncorroborated source, or inferred.
- **Can't verify** — the evidence needed is not in the bundle (listed explicitly).

---

## Q1. What did we actually spend on SaaS tools last quarter?

**Answer: $81,000 as booked in the Q1 2026 P&L; likely true spend $73,500** — the difference ($7,500) is a vendor that appears twice and finance has not yet confirmed against the invoice. Range: **$73,500 – $81,000**.

### How the number is built
- 15 Software & SaaS line items, pnl_q1_2026.csv:L9–L23. Recomputed sum = **$81,000**.
- Listed subtotal $81,000 `pnl_q1_2026.csv:L24` — ties exactly. **Confidence: High** that this is what's booked.
- Scope: Priya Raman — "Software & SaaS line is finalized for Q1, subtotal as listed is $81k for the quarter. Note AWS infra (~$38k) sits under Infrastructure, not here — don't let an…" `slack_export.md:L144` (Priya Raman, 2026-06-02 10:30). So AWS / Cloudflare (Infrastructure) are excluded.

### What we're paying for (as booked)
| Vendor | Q1 USD | Purpose | Source |
|---|---:|---|---|
| Salesforce | $12,000 | CRM; renewal discussion in #finance — see note | `pnl_q1_2026.csv:L9` |
| Looker | $11,000 | BI / dashboards | `pnl_q1_2026.csv:L11` |
| HubSpot | $9,000 | Marketing automation | `pnl_q1_2026.csv:L10` |
| Amplitude | $7,500 | Product analytics | `pnl_q1_2026.csv:L12` |
| Amplitude Analytics | $7,500 | Product analytics | `pnl_q1_2026.csv:L13` |
| Google Workspace | $6,000 | Email / docs / storage | `pnl_q1_2026.csv:L18` |
| Adobe Creative Cloud | $5,400 | Editing / creative suite | `pnl_q1_2026.csv:L15` |
| Slack | $4,200 | Internal comms | `pnl_q1_2026.csv:L17` |
| Greenhouse | $4,000 | ATS / recruiting | `pnl_q1_2026.csv:L22` |
| Figma | $3,600 | Design | `pnl_q1_2026.csv:L14` |
| GitHub | $3,000 | Source control | `pnl_q1_2026.csv:L20` |
| Notion | $2,400 | Docs / wiki | `pnl_q1_2026.csv:L16` |
| Airtable | $2,100 | Ops trackers | `pnl_q1_2026.csv:L23` |
| Zoom | $1,800 | Video calls | `pnl_q1_2026.csv:L19` |
| Sentry | $1,500 | Error monitoring | `pnl_q1_2026.csv:L21` |

### Issues that move the number
- **Possible double-count ($7,500):** "Amplitude" `pnl_q1_2026.csv:L12` + "Amplitude Analytics" `pnl_q1_2026.csv:L13` — identical amount and description.
  - Maya Fortin: "One thing on the SaaS tab — we've got both an "Amplitude" line and an "Amplitude Analytics" line, each at $7.…" `slack_export.md:L147` (Maya Fortin, 2026-06-02 10:38)
  - Priya Raman: "Yeah that smells like a double-count. Pull the Amplitude invoice when you get a sec and we'll fix it if it's …" `slack_export.md:L150` (Priya Raman, 2026-06-02 10:45)
  - Maya Fortin: "Added to my list. Haven't gotten the invoice back yet so I'm leaving the CSV as-is until I can confirm." `slack_export.md:L153` (Maya Fortin, 2026-06-02 10:47)
  - Status: unresolved in the bundle (invoice not received). **Confidence that true spend is $73,500: Medium.**
- **Salesforce renewal:** $60,000/yr ≈ $15,000/qtr vs $12,000 posted `pnl_q1_2026.csv:L9`. Renewal closed **after** Q1 ended, so it does not change Q1 actuals `slack_export.md:L119` (Priya Raman, 2026-05-14 11:02). Q1 posting kept as-is. Run-rate after renewal rises by ≈$3,000/qtr.
  - ⚠ Finance note says the posted figure "looks higher than a $60k annual would imply" `meeting_notes/finance_review_2026-05-28.md:L23` (minutes by Maya Fortin, 2026-05-28) — arithmetic says it is *lower* ($12,000 < $15,000). Note is internally inconsistent; flagged, not relied on.
- Outside SaaS: Cloudflare "€1900" `pnl_q1_2026.csv:L26` is in EUR and un-normalized; not SaaS, not included.

### Could NOT verify
- Vendor invoices / contracts for any line (none in the bundle) — incl. whether Amplitude is one contract.
- Finance says some EU-billed tools arrive in EUR `meeting_notes/finance_review_2026-05-28.md:L25` (minutes by Maya Fortin, 2026-05-28); no SaaS line is marked EUR, so I assume all SaaS lines are already USD. If one isn't, the total moves by the FX difference.
- SaaS paid outside AP (team credit cards, expensed seats) — would not appear in this P&L.
- Whether the P&L is final-final: finance notes are marked "Figures illustrative / pre-close".

---

## Q2. Did we decide to hire in Sales or freeze hiring — current state, and who owns it?

**Answer: Sales hiring is FROZEN** (decided 2026-06-10). **Decision owner: Dana Whitfield** (CEO); **enforcer on reqs: Priya Raman**. REQ-114 (Account Executive) is paused, not cancelled.

**Confidence: High** — 4 independent sources (Dana Whitfield, Elena Novak, Marcus, Priya Raman) state it is frozen on/after the decision; no later statement contradicts it.

### Key evidence
- Decision: "OK, decision on Sales hiring. After the Q1 sales miss we're FREEZING all new Sales headcount until pipeline recovers. No new AE reqs move forward, REQ-114 incl…" `slack_export.md:L67` (Dana Whitfield, 2026-06-10 08:47)
- Ownership stated explicitly `slack_export.md:L79` (Dana Whitfield, 2026-06-10 09:14)
- Enforcement by Priya Raman `slack_export.md:L67` (Dana Whitfield, 2026-06-10 08:47)
- Scope: "Thanks all. To be clear so there's no ambiguity downstream: current state is frozen on Sales hiring, I'm maki…" `slack_export.md:L79` (Dana Whitfield, 2026-06-10 09:14)
- Scope: "No — freeze is Sales-only for now. Other teams' open reqs are unaffected. Just Sales." `slack_export.md:L236` (Elena Novak, 2026-06-11 09:41)
- Scope: "- Scope: net-new Sales reqs only. Backfills for regretted attrition to be reviewed case-by-case by Priya + To…" `meeting_notes/leadership_sync_2026-06-11.md:L17` (minutes by Marcus, 2026-06-11)
- Revisit: "Understood, I'll hold them. Tomás, that means REQ-114 is paused, not killed — we revisit when Q2 pipeline sho…" `slack_export.md:L70` (Priya Raman, 2026-06-10 08:52)
- Revisit: "- Revisit trigger: pipeline coverage back to target + two consecutive months of recovered conversion. Re-eval…" `meeting_notes/leadership_sync_2026-06-11.md:L19` (minutes by Marcus, 2026-06-11)

### Timeline (every Sales-hiring statement found)
| Date | Stance | Who / where | Statement | Source |
|---|---|---|---|---|
| 2026-04-21 | HIRE | Tomás Reyes | Won't argue the number. Two big renewals slipped into Q2 and one logo churned. I still th… | `slack_export.md:L17` (Tomás Reyes, 2026-04-21 09:31) |
| 2026-05-01 | HIRE | headcount roster | REQ-114 Account Executive status=APPROVED target_start=2026-07-15 HM=Tomás Reyes | `headcount_roster.csv:L22` |
| 2026-05-01 | HIRE | Elena Novak | Roster snapshot is locked as of today (2026-05-01). Open reqs captured: a Sales AE (REQ-1… | `slack_export.md:L222` (Elena Novak, 2026-05-01 16:30) |
| 2026-05-01 | HIRE | Tomás Reyes | Good. REQ-114 is the one I care about — need that AE seated by July 15. | `slack_export.md:L225` (Tomás Reyes, 2026-05-01 16:41) |
| 2026-06-10 | FREEZE (decision) | Dana Whitfield | OK, decision on Sales hiring. After the Q1 sales miss we're FREEZING all new Sales headco… | `slack_export.md:L67` (Dana Whitfield, 2026-06-10 08:47) |
| 2026-06-10 | FREEZE | Priya Raman | Understood, I'll hold them. Tomás, that means REQ-114 is paused, not killed — we revisit … | `slack_export.md:L70` (Priya Raman, 2026-06-10 08:52) |
| 2026-06-10 | FREEZE (decision) | Dana Whitfield | Thanks all. To be clear so there's no ambiguity downstream: current state is frozen on Sa… | `slack_export.md:L79` (Dana Whitfield, 2026-06-10 09:14) |
| 2026-06-11 | context | Marcus | - Dana raised the open Sales req (the AE role, REQ-114, Tomás's team) that was approved b… | `meeting_notes/leadership_sync_2026-06-11.md:L15` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | FREEZE (decision) | Marcus | - DECISION: Freeze all new Sales headcount until pipeline recovers. Quote (Dana): *"After… | `meeting_notes/leadership_sync_2026-06-11.md:L16` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | context | Marcus | - Scope: net-new Sales reqs only. Backfills for regretted attrition to be reviewed case-b… | `meeting_notes/leadership_sync_2026-06-11.md:L17` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | FREEZE (decision) | Marcus | - Owner: Decision made by Dana (CEO); Priya (CFO) holds the line / enforces — no new Sale… | `meeting_notes/leadership_sync_2026-06-11.md:L18` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | context | Marcus | - Tomás flagged candidate already in late-stage interviews for REQ-114 — Priya to confirm… | `meeting_notes/leadership_sync_2026-06-11.md:L20` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | context | Marcus | | 1 | Confirm REQ-114 candidate handling (pause vs finish loop, no offer) | Priya + Tomás… | `meeting_notes/leadership_sync_2026-06-11.md:L42` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | context | Marcus | | 2 | Notify Elena/People to pause Sales req in Greenhouse | Marcus | 2026-06-12 | | `meeting_notes/leadership_sync_2026-06-11.md:L43` (minutes by Marcus, 2026-06-11) |
| 2026-06-11 | FREEZE | Elena Novak | Following yesterday's leadership call: Sales hiring is frozen effective immediately. REQ-… | `slack_export.md:L230` (Elena Novak, 2026-06-11 09:30) |
| 2026-06-11 | FREEZE | Elena Novak | No — freeze is Sales-only for now. Other teams' open reqs are unaffected. Just Sales. | `slack_export.md:L236` (Elena Novak, 2026-06-11 09:41) |
| 2026-06-15 | FREEZE | Elena Novak | Q3 planning prep: if you want any new headcount considered, get it to me with justificati… | `slack_export.md:L244` (Elena Novak, 2026-06-15 14:00) |

### Conflicts resolved
- Roster snapshot 2026-05-01 shows **REQ-114 Account Executive status=APPROVED target_start=2026-07-15 HM=Tomás Reyes** `headcount_roster.csv:L22` — superseded by the 2026-06-10 decision; explicitly called stale/superseded in `slack_export.md:L230` (Elena Novak, 2026-06-11 09:30), `meeting_notes/leadership_sync_2026-06-11.md:L16` (minutes by Marcus, 2026-06-11).
- The same decision appears dated 2026-06-10, 2026-06-11 (Slack message vs. written minutes; People's Jun 11 post says "following yesterday's leadership call"). Treated as one decision; earliest timestamp used.

### Could NOT verify
- Whether the decision has changed since the last message in the bundle (2026-06-16) — e.g. at the revisit point named above.
- Open action: "- Tomás flagged candidate already in late-stage interviews for REQ-114 — Priya to confirm whether to pause or…" `meeting_notes/leadership_sync_2026-06-11.md:L20` (minutes by Marcus, 2026-06-11) — completion not evidenced.
- Open action: "- Elena (People) to be looped in so recruiting pauses the req in Greenhouse. Action: Marcus to notify Elena." `meeting_notes/leadership_sync_2026-06-11.md:L21` (minutes by Marcus, 2026-06-11) — completion not evidenced.
- Open action: "| 1 | Confirm REQ-114 candidate handling (pause vs finish loop, no offer) | Priya + Tomás | 2026-06-13 |" `meeting_notes/leadership_sync_2026-06-11.md:L42` (minutes by Marcus, 2026-06-11) — completion not evidenced.
- Greenhouse (ATS) status of REQ-114 — no ATS export in the bundle.
