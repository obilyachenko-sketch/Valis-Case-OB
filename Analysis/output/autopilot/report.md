# Support autopilot — run report

Input: `support_tickets_q1_2026.csv` · 140 rows · 140 processed · 0 quarantined · period 2026-01-02 → 2026-03-31 (12.7 weeks)

## Before → after
| | Before (measured) | After (modelled) | Change |
|---|---:|---:|---:|
| Handle time, quarter | 70.5 h | 40.6 h | **−29.9 h (−42.5%)** |
| Handle time per week | 5.54 h | 3.19 h | −2.35 h |
| Tickets needing a person | 140 | 60.8 (expected) | −79.2 |

**Before** = sum of `Handle_Minutes` on every processed row (measured). **After** = deflected tickets cost `residual_minutes` when the flow works, and full original minutes for the 20% that fall back to a person; everything else unchanged (modelled — see assumptions).

## By category
| Category | Tickets | Route | Before h | After h | Saved h |
|---|---:|---|---:|---:|---:|
| Tax form (W-9/W-8) | 36 | ESIGN_TAX_FORM | 25.9 | 10.0 | 15.9 |
| Thumbnail re-upload | 63 | SELF_SERVE_THUMBNAIL | 22.8 | 8.8 | 14.0 |
| Payout question | 18 | HUMAN | 14.6 | 14.6 | 0.0 |
| Account access | 7 | HUMAN | 2.8 | 2.8 | 0.0 |
| Login issue | 13 | HUMAN | 2.2 | 2.2 | 0.0 |
| Content takedown | 3 | HUMAN | 2.2 | 2.2 | 0.0 |

## Assumptions (not measurable from the bundle) and sensitivity
- Fallback rate (deflected ticket still needs a person, full original minutes): **20%**
- Thumbnail re-upload: residual **5 min** per deflected ticket — Creator swaps the thumbnail via a self-serve link; human only spot-checks. Ops asked for exactly this (slack_export.md:L193).
- Tax form (W-9/W-8): residual **10 min** per deflected ticket — E-sign request + automatic reminder cadence replaces manual chasing; human verifies the returned form. People suggested e-sign services (slack_export.md:L204).

| Fallback rate → | 10% | 20% | 30% | 50% |
|---|---:|---:|---:|---:|
| Saved h / quarter (residual as configured) | 33.7 | 29.9 | 26.2 | 18.7 |
| Saved h / quarter (residual ×2) | 23.6 | 20.9 | 18.3 | 13.1 |

## Actions generated (dry-run outbox)
243 actions for 99 tickets → `outbox.jsonl` (SELF_SERVE_THUMBNAIL: 63, ESIGN_REQUEST: 36, ESIGN_REMINDER: 108, ESCALATE_TO_HUMAN: 36). Nothing is sent; a builder wires these to the CMS self-serve endpoint and an e-sign provider.

## Data quality
- No rows quarantined.
- Warning: TCK-1013 (line 14): blank Assigned_To — kept; effort is still logged
- Warning: TCK-1038 (line 39): blank Assigned_To — kept; effort is still logged
- Warning: TCK-1068 (line 69): blank Assigned_To — kept; effort is still logged
- Warning: TCK-1100 (line 101): blank Assigned_To — kept; effort is still logged

## Out of scope (kept with a person)
- Payout question: Needs the payout tracker, which is not in the bundle (same gap as the brand-deal recon).
- Login issue: Account security - keep human.
- Account access: Account security - keep human.
- Content takedown: Legal/brand judgment - keep human.
