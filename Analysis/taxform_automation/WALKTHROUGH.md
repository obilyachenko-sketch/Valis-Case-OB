# Live walkthrough — 30 minutes, screen-share

The format, from `00_START_HERE.md`: screen-share, reproduce a step or two they pick (possibly on a **fresh file**), then they push on the value number. Everything below runs from the repo root in PowerShell, using only standard Python.

## Before the call (5 min)
```powershell
cd "$HOME\OneDrive\Documents\GitHub\Valis-Case-OB"
git pull                                            # or "Fetch origin" in GitHub Desktop
python --version                                    # 3.9+
python -m unittest discover -s Analysis\tests       # expect: Ran 25 tests ... OK
```
Open in tabs: `Analysis\README.md`, `Analysis\BUILD_LOG.md`, the 4 workbooks in `Analysis\output\`, and `Analysis\output\saas_waterfall.html` and `sales_hiring_timeline.html` in a browser.
**Backup if Python misbehaves:** every output is already committed in `Analysis\output\`, so you can show the files instead.

---

## 0:00–0:03 · Framing (talk, no screen)
- Dana's problem: "I don't trust my own numbers" (`CEO_CONTEXT.md` L7). So every answer here **traces to a file and line**, carries a **confidence level**, and says what I **couldn't verify**.
- Four deliverables: ask-with-sources, a value number, a running automation, a build log. 47 judgment calls are logged.

## 0:03–0:08 · Ask-with-sources (live)
```powershell
python Analysis\ask.py "What did we actually spend on SaaS tools last quarter?"
```
**Expect:** `$81,000 as booked … likely true spend $73,500`. Point at the `pnl_q1_2026.csv:L12` / `L13` citations and the "Could NOT verify" list.
- **Say:** "Booked figure is high confidence; the true figure is medium confidence because the Amplitude invoice was never checked (slack L147–L153)."
- **Show:** `saas_waterfall.png` (81 → −7.5 duplicate → 73.5 → vendors).
```powershell
python Analysis\ask.py "Are we still hiring AEs?"
```
**Expect:** `Sales hiring is FROZEN (decided 2026-06-10). Decision owner: Dana Whitfield … enforcer on reqs: Priya Raman`.
- **Say:** "The roster still says APPROVED. That's the May 1 snapshot, superseded by four later sources."
- **Show:** `sales_hiring_timeline.png`.
```powershell
python Analysis\ask.py "What is our churn rate?"
```
**Expect:** a refusal that lists the bundle files. **Say:** "When the data can't answer, it says so instead of guessing."

## 0:08–0:16 · Automation, shipped and running (live)
```powershell
python Analysis\automation\taxform_chaser.py
notepad Analysis\output\taxform\report.md
```
**Expect:** `before_hours 25.9`, `after_hours 10.0` (−61.5%), `messages_generated 144`.
- **Why this workflow:** the largest measured support category (36 tickets, 1,555 min); Ops flagged it twice (slack L171, L201); People already pointed at e-sign services (L204). The reconciliation ranks higher on criticality but none of its data is in the bundle (`RECON_SCOPE.md`).
- **What it does:** validate → one request per tax-form ticket → e-sign on day 0, reminders on day 3 and 7, hand-off to a person on day 14 → day-by-day replay of Q1 → tracker, chase list, outbox.
- **Be upfront:** "Before is measured. After is modelled: 10 min to check a returned form, 20% handed to a person. Build step 2 logs the return date so both become measured."

**Change it live** (they may ask):
```powershell
python Analysis\automation\taxform_chaser.py --as-of 2026-02-10     # Ops' chase list for that day
```
Edit `Analysis\automation\taxform_config.json` (e.g. `"escalation_rate": 0.5`) and re-run: the saving drops to about 10 h. Undo with `git checkout Analysis\automation\taxform_config.json`.

**Fresh-file drill**, most likely to be asked:
```powershell
python Analysis\automation\taxform_chaser.py --tickets Analysis\taxform_automation\fresh_tickets_practice.csv --out Analysis\output\practice
type Analysis\output\practice\quarantine.csv
```
**Expect:** 8 rows in, **3 quarantined** (duplicate TCK-2004, bad date 2026-04-31, minutes `abc`), 3 tax-form requests, 115 → 47 min.
- **On their file:** (1) open it and check the 7 columns match; (2) run with `--tickets`; (3) read `quarantine.csv` first. If a column is missing, the run fails loudly by design.
- **Fresh bundle for the ask slice:** `python Analysis\ask.py --all --data <their folder>`.

```powershell
python -m unittest discover -s Analysis\tests -v      # 25 acceptance tests
```

## 0:16–0:26 · Value number: let them try to break it
Open `Analysis\output\Value number raw data.xlsx` → **Summary**: **$41,600/yr, support hire avoided** (cost avoidance, not savings). Felt 40 h/week vs measured 5.4 h/week (0.14 FTE).

| They'll say | Answer | Where |
|---|---|---|
| "Tickets miss work done off the system" | At 2× or 3× logged it's still < 0.5 FTE. The 40 h claim needs tickets to capture only 14% of the real effort | Stress tests B4–B6 |
| "There's no req, so you saved nothing" | Agreed, it's a decision avoided; I book it as "req not opened". The hire was gated on this data (slack L179) | Cannot verify #2 |
| "Ops said #47 swaps in one week" | Strongest attack. That's 7.8× Q1's busiest week. If typical: 0.52 FTE manual → **$20,129** floor; with automation 0.26 FTE → $30,991 | Stress tests B16–B23; Summary bounds |
| "Your $41,600 is an average salary" | Yes, $3.12M ÷ 300 × 4. The dollar figure moves with the real role cost; the direction doesn't | Sources rows 3–4 |
| "Q1 is tax season, so you're overstating" | I removed that argument. Tax forms follow onboarding, and Ops says "season again" in June (L201). Neutral | Build log JC-38 |
| "Change an input" | Flip Summary **B11** (incremental FTE) from 0 to 0.14 → value becomes $35,960 | Summary B11 |

**Unblocker to name:** Q2 tickets from Ben Okoro (slack L185). The same scripts re-run unchanged.

## 0:26–0:30 · Build log and judgment calls
Open `Analysis\BUILD_LOG.md`. Pick 3:
- **JC-03:** Amplitude double-count, reported as a range, not silently fixed.
- **JC-19 / JC-36:** the "#47" counter-evidence promoted to the headline risk, with an exact worst case.
- **Self-corrections:** the "#47 = 2.4×" error (it was 10×), and the seasonality claim retracted (JC-38). "I'd rather show you where I was wrong than hide it."

## If they ask…
- **"Why not automate the reconciliation?"** Top on criticality (15/15: 80% of revenue, board numbers, one person). But none of the 3 exports exist in the bundle. It's scoped and ready (`RECON_SCOPE.md`); step 0 is Maya's exports.
- **"What would you do in week 2?"** Get the Q2 tickets and the reconciliation exports; pick an e-sign vendor under the $1,275/yr break-even; turn on `form_returned_date` logging.
- **"How much was AI?"** Built with Claude end to end. I drove it, checked every citation against the source file, and caught its mistakes; the build log shows where.
