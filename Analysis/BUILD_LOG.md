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
| 16:57 | Commit `556baa3` | Log + trail pushed. |

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
- **JC-13** — Liam claims "easily 40 hrs/week" on creator support (slack 176); logged data = 70.5 hrs for the whole quarter ≈ **5.4 hrs/week** (13-week quarter; see JC-18, JC-19). → Use measured figure; flag that tickets may not capture all effort (e.g., un-ticketed chasing). *Reason: Elena asked "measured or a vibe?" — this is the measured answer, ~7× lower.*
- **JC-14** — Biggest time sink candidate is the brand-deal 3-way recon (~3 days/month, Maya; slack 108, 158; finance notes 11–13; leadership notes 35), but the three source systems (CRM export, invoicing sheet, payout tracker) are **not in the bundle**. → Can quantify the time from three consistent mentions but cannot build the matcher on real data without them. *Reason: don't manufacture data; decide approach in next session.*

---

## Session 2 — build the three deliverables

| Time | Step | Detail |
|---|---|---|
| 17:12 | Prompt | "keep the log. 3 outcomes: ask-with-sources slice … value number … automation" (brief deliverables 1–3). |
| 17:13 | Files | `nwlib/sources.py` — loaders that keep provenance (`Cite(file, line, who, when)`) for P&L, roster, Slack, meeting notes, tickets; BOM-aware decoding. |
| 17:14 | Files | `ask.py` — router + two answerers (SaaS spend, Sales hiring). Everything recomputed from raw files per run. |
| 17:15 | First run — 4 bugs | (a) Sales answer anchored on Elena's Jun 11 *relay* ("per Dana's decision") instead of Dana's Jun 10 decision; (b) notes dated at midnight compared against timestamped Slack, dropping same-day evidence; (c) Amplitude duplicate pulled in Ben's unrelated *event* de-dup line; (d) "keep hiring into Sales or hold?" — a question — scored as HIRE. |
| 17:16 | Fix | Decision = first statement of the final stance after the last opposite decision; compare by date; billing-word filter + same-thread invoice follow-ups; questions = context. Dead-end: first patch script aborted on a no-op assert — re-ran without it. |
| 17:16 | Fix | Refusal path listed `.git/hooks/*` as "bundle contents" → `find()` now skips dot-dirs. |
| 17:17 | Commit `e3f5354` | Ask slice. |
| 17:18 | Files | `automation/support_autopilot.py` + `playbooks.json`. First run: 140/140 processed, 70.5 h → 40.6 h, 243 dry-run actions. |
| 17:19 | Tests | `tests/test_all.py` (13 tests). **Mutation test caught a real bug:** adding "Lifting the freeze: REQ-114 approved again" still answered FROZEN (the word *freeze* matched). Added LIFT pattern; also removed three sentences that were hard-coded rather than derived (paused-not-cancelled, "three sources call roster stale", July revisit). |
| 17:19 | Commit `f80a947` | Autopilot + builder spec + tests. |
| 17:20 | Files | `value_number.py` → `VALUE_NUMBER.md`, `output/value_source_rows.csv`. |
| 17:20 | Correction | I had written from memory that Ops' "#47 this week" was ~2.4× Q1's rate. Recomputed: Q1 = 4.8 thumbnails/week → **~10×**. Promoted it from footnote to the headline risk, with its own computed scenario. |
| 17:21 | Files | This log updated; `Analysis/README.md`. |

## Judgment calls (session 2)

- **JC-15 — Automation target.** Largest *claimed* sink is brand-deal recon (~3 days/month, 4 consistent mentions), but its 3 inputs (CRM export, invoicing sheet, payout tracker) are not in the bundle. Brief requires it to run on this data → chose creator-support deflection (tax forms + thumbnails = 69% of measured support minutes). *Reason: biggest workflow I can run on real rows; recon stays #2 and is named in the spec.*
- **JC-16 — Value number = support hire avoided ($41,600/yr), booked as cost avoidance, not savings.** Alternatives rejected: Amplitude $30k/yr (can't tell cash leak from booking error without the invoice); autopilot hours × $20/h ≈ $2.4k/yr (true but trivial). *Reason: every input is a raw row, and it informs a live decision (L179, L244).*
- **JC-17 — Loaded cost per FTE = P&L salaries $3.12M ÷ roster TOTAL 300 × 4 = $41,600.** Company average, not the role's cost; P&L says "~300". *Reason: only cost basis in the bundle; listed as unverified.*
- **JC-18 — Weeks per quarter = 13** for the value number (finance convention → 5.42 h/wk). The autopilot report uses the data span (Jan 2–Mar 31 = 12.7 wks → 5.54 h/wk). *Reason: both shown; the difference doesn't change any conclusion.*
- **JC-19 — "#47 this week" (L193) is treated as possible Q2 counter-evidence, not dismissed.** If weekly and typical → 20.6 h/wk manual (0.52 FTE), 10.2 h/wk with the autopilot. Confidence on the value number lowered to **Medium**. *Reason: Q2 tickets aren't in the bundle; a finance reviewer would find this line.*
- **JC-20 — `Handle_Minutes` are all multiples of 5 (10–55).** Treated as estimates, not timers. *Reason: verified on all 140 rows; listed as unverified precision.*
- **JC-21 — Payout questions are out of automation scope** (14.6 h). *Reason: answering needs the payout tracker, same missing input as the recon.*
- **JC-22 — Autopilot "after" is modelled.** Fallback 20%, residual 5/10 min are assumptions in `playbooks.json`, with a sensitivity table (13.1–33.7 h saved/qtr). *Reason: no post-automation data can exist yet; the spec makes measuring them step 4.*
- **JC-23 — Meeting-note lines are dated by filename; "who" = the note-taker.** *Reason: notes have no per-line timestamps; citing the scribe keeps them distinct from the speaker's own Slack post.*
- **JC-24 — Confidence for Sales = High**, computed: 4 independent sources (Dana, Priya, Elena, leadership minutes) on/after the decision, no later contradiction. *Reason: rubric is in the code, not hand-assigned.*

## Open / next

- Pull Q2 support tickets and re-run `value_number.py` + autopilot unchanged (resolves JC-19).
- Amplitude invoice → resolves the $7,500 SaaS range.
- Get the three recon exports → build the 3-way matcher (next automation).

---

## Session 3 — question-by-question review

| Time | Step | Detail |
|---|---|---|
| 17:35 | Prompt | "go question by question… start with SaaS spend" (+ user's analysis skill: ranked evidence, facts vs judgment, confidence, math, bounds). Answered in chat. |
| 17:44 | Prompt | "show me raw data in excel, include commentary with reference when there is conflicting data" |
| 17:47 | Files | `build_saas_workbook.py` → `output/SaaS_Q1_2026_raw_data.xlsx`: Summary (9 live formulas, recalculated, 0 errors), P&L raw (all 34 rows unchanged incl. '€1900' text and blanks, with flags + cell comments), Evidence (14 Slack/notes lines quoted with file:line), Conflicts (C1–C5). |

- **JC-25** — In the workbook, raw values are kept exactly as exported (Cloudflare stays the text '€1900', blanks stay blank). Only the Summary tab interprets them. *Reason: the user asked for raw data; interpretation must stay separable and visible.*
- **JC-26** — Data-review L36 (Amplitude *event* duplicates) is listed in Evidence but marked "NOT the billing duplicate". *Reason: same vendor name and the word "duplicate" make it easy to conflate; my first parser did exactly that (17:15).*
| 17:57 | Prompt | "Generate a waterfall graph from the data below. highlight second amplitude duplicate in red" (user pasted the 15 SaaS rows + subtotal, EU number format: $12.000 = $12,000). |
| 18:02 | Files | `output/saas_waterfall.html` (interactive: hover tooltips with source line, table view, dark mode) + `output/saas_waterfall.png`. Palette validated (blue #2a78d6 vs red #d03b3b: CVD ΔE 23.8, PASS). First render: legend broken and "$73,500" label collided with bars → moved label right of the subtotal bar. |

- **JC-27** — Pasted values match `pnl_q1_2026.csv` L9–L24 exactly (read "$12.000" as twelve thousand, EU separators). Chart kept in P&L order and running total checked = $81,000 = listed subtotal. Duplicate shown red **plus** hatch + ⚠ label (not colour alone). "Without duplicate $73,500" is a reference line, not an extra bar. *Reason: chart shows the data as given and makes the open question visible without restating the ledger.*
| 18:02 | Prompt | "redraft: start with 81, minus 7.5 Amplitude duplicate, then 73 correct spend, then deduct correct spend highest→lowest" |
| 18:06 | Files | Waterfall redrafted: Booked $81,000 → −$7,500 duplicate (red, hatched) → Correct spend $73,500 → 14 vendors deducted, sorted high→low, closing at $0 (checked in code; warns if it doesn't). Fixed label collision at the top-left and clipped axis labels. |
| 18:07 | Prompt | "make 81 dashed grey. 73 blue as the rest of software. All titles vertical and bigger font" |
| 18:09 | Files | Booked $81,000 → light-grey fill with dashed grey outline; Correct spend $73,500 → same blue as vendors; x-axis labels vertical at 15px (was 12px, −38°). Legend updated to match. |
