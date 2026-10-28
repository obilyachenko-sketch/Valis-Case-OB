# Scope — Brand-deal revenue reconciliation (3-way match)

**Status:** scoped, not built. All three inputs are missing from the bundle (see §4).
**Owner:** Maya Fortin (Finance Analyst) · **Sponsor:** Priya Raman (CFO) · **Review forum:** Marcus Lindqvist's ops/automation review (`leadership_sync_2026-06-11.md` L35)

## 1. Problem: what the data says

| Fact | Source |
|---|---|
| Every month-end, Maya ties out brand-deal revenue across **three sources that never agree on the first pass**: the CRM export ("what Sales says closed"), the invoicing sheet ("what we billed") and the payout tracker ("what creators actually got paid against deals") | `slack_export.md` L97, L100 |
| Takes **~3 full days every close**: April, May, "same as the last few months" | `slack_export.md` L108, L158; `finance_review_2026-05-28.md` L11 |
| What drifts: **deal amounts, close dates, payout splits**. Today it's a manual line-by-line tie-out | `finance_review_2026-05-28.md` L12 |
| CFO: "the single biggest finance time-sink… only going to get worse as brand-partnership volume grows"; top automation candidate | `finance_review_2026-05-28.md` L13; `slack_export.md` L111 |
| Maya: automating the 3-way match = "three days a month back and the numbers would actually be trustworthy on the first pass" | `slack_export.md` L114 |
| Scale: brand partnerships = **$4.2M of $5.25M Q1 revenue (80%)**, booked *net of agency commissions* | `pnl_q1_2026.csv` L2, L5 |
| CRM is Salesforce | `pnl_q1_2026.csv` L9 |

**Why it's first:** it scores **15/15 on business criticality** (`Time waste raw data.xlsx` → Workflows, W1): core revenue, board-level numbers, month-end deadline, one person, getting worse. On hours it ties with creator support (~72 vs 70.5 h a quarter).

## 2. Outcome: before → after

| | Before | Target after v1 | Basis |
|---|---|---|---|
| Maya's time per close | ~3 days (bounds 45–84 h a quarter) | **≤ 0.5 day** reviewing exceptions only | Before: slack L108. After: target, to be measured in parallel runs |
| First-pass tie-out | Never | Every source row either matched or explained by a coded exception | slack L97; finance_review L12 |
| Brand-partnership revenue ↔ P&L | Manual | Invoiced total reconciles to the P&L line, with the difference itemised | pnl L2 |

Value in dollars is small: about 2.5 days × 8 h × 12 months × $20/h ≈ **$4,800 a year**. The case rests on accuracy, close speed and the key-person risk.

## 3. Scope

| In (v1) | Out (v1) |
|---|---|
| Ingest the 3 monthly exports, validate against the data contract, quarantine bad rows with reasons | Changing Salesforce, invoicing or payout *processes* |
| Match CRM ↔ invoice ↔ payout per deal; tolerances in config | Writing back to any system (read-only) |
| Coded exception queue with a suggested fix per exception | Revenue recognition policy decisions (stay with Priya) |
| Month-end tie-out summary vs the P&L brand-partnerships line | Creator subscriptions and "other" revenue |
| Audit trail: every output row traces to source file + row | Payout *execution* |
| Parallel run alongside Maya's manual recon for 2 closes | FX beyond flagging non-USD rows (until it's confirmed whether deals are multi-currency) |

**Phase 2 (after v1):** expose per-deal payout status, so support can answer "where's my payout?" (14.6 h a quarter of tickets, `support_tickets_q1_2026.csv`). This is my inference that the same data serves both uses; nobody in the bundle says so.

## 4. Data contract: **PROPOSED**, to confirm with Maya

None of these files is in the bundle. Field names below are placeholders for the *information* the data says is compared: amount, close date, payout split. Rows marked ❓ are open questions.

**A. CRM deal export (Salesforce), "what Sales says closed"**
| Field | Type | Rule |
|---|---|---|
| `deal_id` | string | unique; ❓ is the same ID carried on invoices and payouts? |
| `brand` | string | non-blank |
| `creator_id` | string | ❓ one creator per deal, or several? |
| `close_date` | date | ISO; drives the month the deal belongs to |
| `deal_amount` | number | ❓ gross or net of agency commission? (P&L is net, L2) |
| `currency` | string | default USD; ❓ any non-USD deals? |
| `stage` | string | only Closed-Won rows are in scope |

**B. Invoicing sheet, "what we billed"**
| Field | Type | Rule |
|---|---|---|
| `invoice_id` | string | unique |
| `deal_id` | string | ❓ present? If not → fallback match (§5) |
| `brand` | string | |
| `invoice_date` | date | |
| `invoice_amount` | number | ❓ gross or net? |
| `agency_commission` | number | ❓ itemised? Needed to reconcile to the P&L net figure |
| `status` | string | issued / paid / void; void excluded |

**C. Payout tracker, "what creators actually got paid against deals"**
| Field | Type | Rule |
|---|---|---|
| `payout_id` | string | unique |
| `deal_id` | string | ❓ present? |
| `creator_id` | string | |
| `payout_date` | date | |
| `payout_amount` | number | |
| `split_pct` | number | ❓ the "payout split" that drifts (finance_review L12): where is the agreed split recorded? |

Any missing required column fails the whole run; nothing partial is produced. This is the same rule as the support automation's contract (`BUILDER_SPEC.md`).

## 5. Matching rules (configurable)
1. **Primary:** join on `deal_id` across all three.
2. **Fallback** (if invoices or payouts lack `deal_id`): brand + creator + amount within tolerance + date within window. Fallback matches are flagged "fuzzy" for review.
3. **Tolerances** (starting values; tune on the first parallel run): amount ±$1 or ±0.5%; date window ±31 days, to catch month-boundary cut-off.
4. **Split check:** sum of payouts per deal = invoiced net × agreed creator split, within tolerance.

## 6. Exception codes (each one is a row in the queue with a suggested fix)
| Code | Meaning | Likely fix owner |
|---|---|---|
| `NO_INVOICE` | Closed in CRM, not invoiced | Finance |
| `NO_CRM` | Invoiced, not closed in CRM | Sales ops |
| `NO_PAYOUT` / `PAYOUT_NO_DEAL` | Payout missing / payout without a deal | Finance / Talent |
| `AMOUNT_MISMATCH` | CRM vs invoice amount outside tolerance | Sales ops / Finance |
| `PERIOD_MISMATCH` | Close date and invoice in different months (cut-off) | Finance |
| `SPLIT_MISMATCH` | Payouts ≠ agreed split | Talent / Finance |
| `GROSS_NET` | Difference explained by agency commission | Auto-explained if commission is itemised |
| `DUPLICATE` | Same deal/invoice/payout twice | Source owner |
| `FX` | Non-USD row | Finance |

## 7. Outputs
`matched.csv` (one row per deal, with all three source refs) · `exceptions.csv` (code, amounts, source rows, suggested fix) · `tieout.md` (CRM total vs invoiced vs paid vs P&L brand-partnerships line, with each difference itemised by exception code) · `quarantine.csv` · `audit.jsonl`.

## 8. Acceptance test: "answer-complete"
1. **Every row of every source is accounted for:** matched, or in exactly one exception, or quarantined with a reason.
2. **Totals tie:** CRM, invoiced and paid totals each equal the sum of their matched and exception rows; the invoiced net total reconciles to the P&L brand-partnerships line (Q1: $4,200,000, `pnl_q1_2026.csv` L2) or the gap is fully itemised.
3. **Each exception code is caught** on a seeded fixture with one known case of each.
4. **Idempotent:** a re-run on the same inputs gives identical outputs.
5. **Parallel run:** on one real close, every discrepancy Maya finds by hand appears in `exceptions.csv`, with no unexplained extras.
6. **Done (v1)** = tests green + two consecutive closes where Maya's time is ≤ 0.5 day, measured by her own log.

## 9. Plan
| Step | What | Unblocks |
|---|---|---|
| 0 | Maya shares April + May exports of all three sources and her written-up steps (action due before June close, `finance_review` L36) | Everything |
| 1 | Confirm the data contract (§4 ❓s) with Maya; freeze `recon.config.json` | Build |
| 2 | Build matcher + fixtures + acceptance tests; run on April and May history | Parallel run |
| 3 | Parallel run on the June close; tune tolerances | Go-live |
| 4 | Live from the July close; Phase 2 payout-status feed for support | Support deflection |

**Builder estimate:** my judgment, not from the data: about 3–5 days for v1 *after* step 1. Most of the risk is in §4, not the code.

## 10. Open questions for Maya (from the ❓s)
1. Is `deal_id` (Salesforce Opportunity ID) on invoices and payouts?
2. CRM amounts: gross or net of agency commission? Is commission itemised anywhere?
3. Where is each deal's agreed creator split recorded?
4. Can one deal have several creators, invoices or payouts?
5. Any non-USD deals?
6. Which discrepancies do you fix in the source system, and which do you only note?
7. What do you look at first when the totals don't tie? This becomes the default exception order.

## 11. Risks
- **No shared deal ID:** fallback fuzzy matching is slower to trust. Mitigation: flag fuzzy matches; ask Sales ops to add the ID to the invoice template.
- **Gross vs net:** if commission isn't itemised, the P&L tie-out stays manual. Mitigation: add a column to the invoicing sheet.
- **Key-person risk during build:** Maya is both the user and the only source of rules. Mitigation: step 0 write-up first, as Priya already asked (`finance_review` L13).
