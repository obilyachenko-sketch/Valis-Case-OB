# Tax-form chasing (W-9 / W-8) — automation

**Selected and confirmed 2026-10-28.** It replaces manual chasing of creators' tax forms with an e-sign request plus automatic reminders, and hands the request to a person only if the form doesn't come back.

## Results on the real Q1 data (140 tickets, 36 of them tax forms)
- **25.9 h → 10.0 h per quarter (−61%)**: 1.99 → 0.77 h a week
- **36 manual chase threads → ~7 hand-offs** to a person
- **Cadence:** e-sign request on day 0 → reminders on day 3 and 7 → a person on day 14 (144 messages, dry-run)
- **Pays back** if the e-sign tool costs **< $1,275 / year**
- **25 acceptance tests pass**

Before is measured from the ticket log. After is modelled: 10 min to check a returned form, 20% handed to a person. Logging the form-return date (build step 2) turns both into measured numbers.

## In this folder
| File | What it is |
|---|---|
| [WALKTHROUGH.md](WALKTHROUGH.md) | 30-minute live walkthrough script: commands, expected output, likely questions |
| [TAXFORM_BUILDER_SPEC.md](TAXFORM_BUILDER_SPEC.md) | One-page builder spec: scope, data contract, acceptance test, in/out |
| [DECISIONS.md](DECISIONS.md) | Why this workflow: all 8 candidates, and why reconciliation was dismissed (data missing) |
| [fresh_tickets_practice.csv](fresh_tickets_practice.csv) | Practice file for the "fresh file" drill: 8 rows, 3 deliberately broken |

## Code and outputs (kept in place so the commands keep working)
| Link | What it is |
|---|---|
| [taxform_chaser.py](../automation/taxform_chaser.py) | The automation |
| [taxform_config.json](../automation/taxform_config.json) | Cadence and assumptions; edit to try what-ifs |
| [report.md](../output/taxform/report.md) | Run report: before → after, sensitivity, break-even |
| [tracker.csv](../output/taxform/tracker.csv) · [outbox.jsonl](../output/taxform/outbox.jsonl) · [replay_by_day.csv](../output/taxform/replay_by_day.csv) | One row per request · every message · what happened each day |
| [test_taxform.py](../tests/test_taxform.py) | Acceptance tests |

## Run it
```bash
python Analysis/automation/taxform_chaser.py
python -m unittest discover -s Analysis/tests
```
