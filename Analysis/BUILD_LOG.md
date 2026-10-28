# Build Log — Valis case (Northwind-in-a-box)

Running, timestamped log of prompts, files created, dead-ends and every judgment call on the dirty data.
Times are Europe/Amsterdam (CET), 2026-10-28. Tooling: Claude (Claude Code cloud session + desktop app bridge to local folder), git/GitHub.

Format for judgment calls: **JC-nn** — what looked wrong → what I decided → one-line reason.

---

## Session 1 — setup and first read

| Time | Step | Detail |
|---|---|---|
| 16:17 | Prompt | "push all updates to my GitHub project" — link pointed to a GitHub *Project board*, not a repo. |
| 16:18 | Dead-end | Project boards can't hold files; Claude can't create repos (API scoped to attached repos). Tried browser route — Chrome extension not connected; built-in browser reached GitHub login. Stopped there (no password entry by the agent). |
| 16:30 | Repo | User created `obilyachenko-sketch/Valis-Case-OB`. Cloned; verified all 11 bundle files byte-identical (md5) to local folder. |
| 16:40 | Dead-end | Push refused (403) — Claude GitHub App not installed. GitHub Desktop install doesn't grant it. |
| 16:52 | Fix | App installed; push dry-run accepted. |
| 16:54 | Commit `1d7b6ba` | Flattened `Northwind-in-a-box (3)/Northwind-in-a-box/` to repo root (pure renames, no content change). |
| 16:55 | Commit `3cefe1b` | Created `Analysis/` for all outputs. |
| 16:56 | Prompt | "open the main questions. Generate trail" |
| 16:56 | Read | All 11 source files read in full with line numbers (`cat -n`); CSVs profiled in Python. |
| 16:57 | Files | Created `Analysis/BUILD_LOG.md` (this file) and `Analysis/EVIDENCE_TRAIL.md` (per-question source map). |

## Judgment calls on the data (so far)

- **JC-01** — `CEO_QUESTIONS.md` is UTF-16 LE with CRLF; every other file is UTF-8 → convert to UTF-8 in a scratch copy for parsing, leave original untouched. *Reason: tools mis-read UTF-16 as garbage; source must stay as delivered.*
- **JC-02** — `CEO_QUESTIONS.md` has 2 numbered questions + an unnumbered "Workflow" section; `00_START_HERE.md` says "two questions" plus separate value-number and automation deliverables → treat Q1 (SaaS) and Q2 (Sales hiring) as the ask-with-sources questions; "Workflow" feeds deliverables 2 and 3. *Reason: matches the brief's own structure.*
- **JC-03** — P&L SaaS "subtotal" $81,000 includes both `Amplitude` (line 12) and `Amplitude Analytics` (line 13), $7,500 each; finance flagged likely double-count but never confirmed (slack 147–153) → report $81,000 as-booked AND $73,500 if de-duplicated; do not silently pick one. *Reason: invoice not seen; CEO asked for "doesn't reconcile and why" over a clean wrong number.*
- **JC-04** — Arithmetic check: 15 SaaS line items sum to exactly $81,000 (subtotal is internally consistent). *Reason: rules out a typo in the subtotal itself.*
- **JC-05** — Cloudflare (`€1900`, P&L line 26) and AWS ($38k, line 25) excluded from SaaS → kept under Infrastructure. *Reason: CFO explicitly says don't fold infra into SaaS (slack 144); category in P&L agrees.* Note the € value is a text-with-symbol cell and Infrastructure subtotal is blank pending FX.
- **JC-06** — Salesforce: P&L Q1 = $12,000 (≈ $48k/yr run-rate); renewal at $60k/yr closed 2026-05-14 (slack 119, finance notes 23). Finance note says posted figure "looks higher than a $60k annual would imply" — but $12k/qtr is *lower* than $15k/qtr. → Keep $12,000 for Q1 (renewal is Q2-dated and doesn't restate Q1); flag the finance note's claim as internally inconsistent. *Reason: renewal post-dates the quarter; the stated discrepancy direction is wrong on its face.*
- **JC-07** — "EU-billed tools come through in EUR; normalize before they hit the SaaS subtotal" (finance notes 25), yet no SaaS line carries a € marker → assume SaaS lines are USD as-posted; list as unverified. *Reason: only Cloudflare is visibly EUR, and it's infra.*
- **JC-08** — Sales hiring: roster (2026-05-01) shows REQ-114 `APPROVED`; superseded by freeze decided 2026-06-10 (slack 66–79), echoed in #people 2026-06-11 (slack 229–236) and leadership sync 2026-06-11 (notes 16). → Most recent, decision-labelled sources win; roster treated as stale. *Reason: three later sources agree and explicitly say the roster is superseded.*
- **JC-09** — Date conflict: Slack has Dana's freeze message on Wed **Jun 10**; leadership-sync notes dated **2026-06-11 (Thu)** record the same decision, and Elena (Jun 11) says "following yesterday's leadership call". → Decision date = 2026-06-10; the 06-11 notes are the formal minute. *Reason: two sources point to Jun 10; notes may be written up a day later.* Low impact on the answer.
- **JC-10** — Roster's open reqs list REQ-118 (Eng), REQ-121 (Content), REQ-125 (Data); Elena's May 1 post mentions "a Creator Management backfill" not in the roster, and omits Content/Data reqs. → Note discrepancy; not material to the Sales answer. *Reason: shows the roster isn't the full req picture.*
- **JC-11** — Roster dirty rows: Felix Braun start date `2026-13-02` (invalid month), Jonas Vik blank start date, team names inconsistent (`Creator Mgmt` vs `Creator Management`). Roster lists only 29 named people vs TOTAL 300 → named list is a sample, not the population; summary counts used for headcount. *Reason: can't derive 300 from 29 rows.*
- **JC-12** — Support tickets: 140 rows, Q1-only (2026-01-02 → 03-31), no duplicate IDs/rows, minutes all 10–55. 4 rows have blank `Assigned_To` (TCK-1013, -1038, -1068, -1100), 2 are `Open` (TCK-1127, -1128). → Keep all in time totals. *Reason: handle minutes are present; assignment blank doesn't change effort.*
- **JC-13** — Liam claims "easily 40 hrs/week" on creator support (slack 176); logged data = 70.5 hrs for the whole quarter ≈ **5.4 hrs/week**. → Use measured figure; flag that tickets may not capture all effort (e.g., un-ticketed chasing). *Reason: Elena asked "measured or a vibe?" — this is the measured answer, ~7× lower.*
- **JC-14** — Biggest time sink candidate is the brand-deal 3-way recon (~3 days/month, Maya; slack 108, 158; finance notes 11–13; leadership notes 35), but the three source systems (CRM export, invoicing sheet, payout tracker) are **not in the bundle**. → Can quantify the time from three consistent mentions but cannot build the matcher on real data without them. *Reason: don't manufacture data; decide approach in next session.*

## Open / next

- Write Q1 and Q2 answers with line-level citations + confidence (deliverable 1).
- Choose value number (deliverable 2) and automation target (deliverable 3) — see JC-13/JC-14 trade-off.
