#!/usr/bin/env python3
"""Tax-form chaser (W-9 / W-8): replaces manual chasing with an e-sign request + automatic reminders.

Runs end-to-end on support_tickets_q1_2026.csv (or any file with the same columns):
  1. ingest + validate against the data contract      -> quarantine.csv (bad rows never dropped silently)
  2. select tax-form tickets (Category ~ ^Tax form)    -> one form request per ticket
  3. build each request's schedule: e-sign request on the ticket date, reminders on day 3/7/14,
     hand-off to a person on day 21 if the form still isn't back
  4. REPLAY the whole period day by day: what the chaser sends each day, and the chase list Ops would see
  5. BEFORE (measured Handle_Minutes) -> AFTER (modelled) with a sensitivity grid and break-even budget

Nothing is sent: messages go to outbox.jsonl (dry-run). Standard library only.

Usage:
    python Analysis/automation/taxform_chaser.py
    python Analysis/automation/taxform_chaser.py --tickets new.csv --as-of 2026-04-15 --out DIR
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE.parent
ROOT = A.parent
sys.path.insert(0, str(A))
sys.path.insert(0, str(HERE))
from support_autopilot import load  # noqa: E402  (shared data-contract validation)
from nwlib.sources import load_pnl, load_doc  # noqa: E402


def loaded_cost_per_hour(root: Path, cfg: dict) -> tuple[float, str]:
    """$ per hour from the P&L personnel line and roster headcount (same basis as the value number)."""
    sal = next(r for r in load_pnl(root) if r.category.lower() == "personnel" and "salar" in r.item.lower())
    doc = load_doc(root, root / "headcount_roster.csv")
    ln = next(i for i, l in enumerate(doc.lines, 1) if l.startswith("TOTAL,"))
    fte = int(doc.line(ln).split(",")[1])
    per_year = sal.amount.value / fte * 4
    return per_year / (52 * cfg["fte_hours_per_week"]), f"{sal.cite} ÷ `{doc.rel}:L{ln}` × 4 ÷ 2,080 h"


def schedule(r: dict, cfg: dict) -> list[dict]:
    d0 = date.fromisoformat(r["Date"])
    rid = "TF-" + r["Ticket_ID"]
    ev = [{"request_id": rid, "ticket": r["Ticket_ID"], "day": 0, "date": d0.isoformat(), "type": "ESIGN_REQUEST",
           "to": r["Submitted_By"], "template": "tax_form_esign_v1",
           "body": (f"Hi @{r['Submitted_By']} — to get paid we need your tax form: W-9 if you're a US person, W-8BEN if not. "
                    f"It takes about 3 minutes in this secure e-sign link: [e-sign link {rid}]. Reply here if you're unsure which one.")}]
    for n, dd in enumerate(cfg["reminder_days"], 1):
        ev.append({"request_id": rid, "ticket": r["Ticket_ID"], "day": dd, "date": (d0 + timedelta(days=dd)).isoformat(),
                   "type": f"REMINDER_{n}", "to": r["Submitted_By"], "template": "tax_form_reminder_v1",
                   "condition": "send only if the form has not been returned"})
    dd = cfg["escalate_after_days"]
    ev.append({"request_id": rid, "ticket": r["Ticket_ID"], "day": dd, "date": (d0 + timedelta(days=dd)).isoformat(),
               "type": "HANDOFF_TO_PERSON", "to": r["Assigned_To"] or "Ops Support",
               "condition": "only if the form is still not returned — a person takes over with full history"})
    return ev


def after_minutes(before: float, rate: float, residual: float) -> float:
    return (1 - rate) * residual + rate * before


def run(tickets: Path, cfg: dict, out: Path, as_of: date | None = None, root: Path = ROOT) -> dict:
    good, bad, warnings = load(tickets)
    pat = re.compile(cfg["category_pattern"], re.I)
    tax = sorted([r for r in good if pat.search(r["Category"])], key=lambda r: (r["Date"], r["Ticket_ID"]))
    if not tax:
        raise SystemExit("no tax-form tickets in input")
    out.mkdir(parents=True, exist_ok=True)
    dates = [date.fromisoformat(r["Date"]) for r in good]
    start, end = min(dates), max(dates)
    as_of = as_of or end

    # ---------------------------------------------------------------- schedule + tracker
    events = [e for r in tax for e in schedule(r, cfg)]
    events.sort(key=lambda e: (e["date"], e["request_id"], e["day"]))
    rate, res = float(cfg["escalation_rate"]), float(cfg["residual_minutes"])
    tracker = []
    for r in tax:
        evs = [e for e in events if e["ticket"] == r["Ticket_ID"]]
        sent = [e for e in evs if date.fromisoformat(e["date"]) <= as_of]
        last = sent[-1]["type"] if sent else "NOT_STARTED"
        nxt = next((e for e in evs if date.fromisoformat(e["date"]) > as_of), None)
        tracker.append({
            "request_id": "TF-" + r["Ticket_ID"], "ticket": r["Ticket_ID"], "source_line": r["source_line"],
            "creator": r["Submitted_By"], "opened": r["Date"], "ticket_status": r["Status"],
            "form": "W-9 or W-8BEN (creator selects)", "steps_by_as_of_if_never_returned": len(sent), "last_step_if_never_returned": last,
            "next_step_if_not_returned": nxt["type"] if nxt else "—", "next_step_date": nxt["date"] if nxt else "—",
            "before_min": r["Handle_Minutes"], "after_min": round(after_minutes(r["Handle_Minutes"], rate, res), 2)})

    # ---------------------------------------------------------------- day-by-day replay
    by_day = defaultdict(list)
    for e in events:
        by_day[e["date"]].append(e)
    replay = []
    d = start
    horizon = max(as_of, end) + timedelta(days=cfg["escalate_after_days"])
    while d <= horizon:
        evs = by_day.get(d.isoformat(), [])
        c = Counter(e["type"].split("_")[0] for e in evs)
        replay.append({"date": d.isoformat(), "in_period": d <= end, "esign_requests": c.get("ESIGN", 0),
                       "reminders": c.get("REMINDER", 0), "handoffs": c.get("HANDOFF", 0),
                       "chase_list": ";".join(e["request_id"] for e in evs if e["type"].startswith("HANDOFF"))})
        d += timedelta(days=1)
    chase_today = [e for e in by_day.get(as_of.isoformat(), []) if e["type"] != "ESIGN_REQUEST"]

    # ---------------------------------------------------------------- write outputs
    def write_csv(name, rows, cols=None):
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols or (list(rows[0]) if rows else ["empty"]), extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    write_csv("tracker.csv", tracker)
    write_csv("replay_by_day.csv", replay)
    write_csv(f"chase_list_{as_of.isoformat()}.csv", chase_today,
              ["request_id", "ticket", "type", "to", "date", "condition"])
    write_csv("quarantine.csv", bad, ["Ticket_ID", "Date", "Category", "Submitted_By", "Assigned_To", "Handle_Minutes",
                                      "Status", "source_line", "errors"])
    with open(out / "outbox.jsonl", "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")

    # ---------------------------------------------------------------- before -> after
    before = sum(r["Handle_Minutes"] for r in tax)
    after = sum(t["after_min"] for t in tracker)
    weeks = cfg["weeks_per_quarter"]
    usd_h, usd_src = loaded_cost_per_hour(root, cfg)
    n = len(tax)
    sens = {f"{er:.0%}": {str(rm): round((before - sum(after_minutes(r["Handle_Minutes"], er, rm) for r in tax)) / 60, 1)
                          for rm in cfg["sensitivity"]["residual_minutes"]}
            for er in cfg["sensitivity"]["escalation_rate"]}
    months = defaultdict(lambda: [0, 0, 0.0])
    for r, t in zip(tax, tracker):
        m = months[r["Date"][:7]]
        m[0] += 1
        m[1] += r["Handle_Minutes"]
        m[2] += t["after_min"]
    summary = {
        "input_rows": len(good) + len(bad), "quarantined": len(bad), "tax_form_tickets": n,
        "distinct_creators": len({r["Submitted_By"] for r in tax}), "period": [start.isoformat(), end.isoformat()],
        "as_of": as_of.isoformat(),
        "before_minutes": before, "after_minutes": round(after, 1),
        "before_hours": round(before / 60, 1), "after_hours": round(after / 60, 1),
        "saved_hours": round((before - after) / 60, 1), "saved_pct": round(100 * (before - after) / before, 1),
        "before_h_per_week": round(before / 60 / weeks, 2), "after_h_per_week": round(after / 60 / weeks, 2),
        "manual_chase_threads_before": n, "handoffs_expected_after": round(rate * n, 1),
        "messages_generated": len(events), "loaded_usd_per_hour": round(usd_h, 2),
        "time_cost_per_year_before": round(before / 60 * 4 * usd_h), "saving_per_year": round((before - after) / 60 * 4 * usd_h),
        "sensitivity_saved_hours": sens,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    c = Counter(e["type"] for e in events)
    L = ["# Tax-form chaser — run report\n",
         f"Input `{tickets.name}`: {summary['input_rows']} rows, {len(bad)} quarantined · **{n} tax-form tickets** from "
         f"{summary['distinct_creators']} creators · period {start} → {end} · tracker as of **{as_of}**\n",
         "## Before → after (per quarter)",
         "| | Before (measured) | After (modelled) | Change |", "|---|---:|---:|---:|",
         f"| Handle time | {before/60:.1f} h | {after/60:.1f} h | **−{(before-after)/60:.1f} h (−{summary['saved_pct']}%)** |",
         f"| Per week | {before/60/weeks:.2f} h | {after/60/weeks:.2f} h | −{(before-after)/60/weeks:.2f} h |",
         f"| Manual chase threads | {n} | {rate*n:.1f} hand-offs (expected) | −{n - rate*n:.1f} |",
         f"| Time cost per year @ ${usd_h:.0f}/h | ${summary['time_cost_per_year_before']:,} | "
         f"${summary['time_cost_per_year_before'] - summary['saving_per_year']:,} | **−${summary['saving_per_year']:,}** |",
         "", f"**Before** = sum of `Handle_Minutes` on the {n} tax-form rows (measured). **After** = for each request, "
         f"{res:.0f} min to check the returned form, or the original minutes if it's handed to a person ({rate:.0%} assumed). "
         f"Loaded $/h: {usd_src}.\n",
         f"**Break-even:** an e-sign/tax-form service pays for itself on time alone if it costs less than "
         f"**${summary['saving_per_year']:,}/year** — the time saved, not the full ${summary['time_cost_per_year_before']:,}, because "
         f"checking returned forms and hand-offs still cost time. People called these services 'cheap' (`slack_export.md:L204`); "
         "no price in the data.\n",
         "## By month", "| Month | Tickets | Before h | After h |", "|---|---:|---:|---:|"]
    for k, (cnt, b, a) in sorted(months.items()):
        L.append(f"| {k} | {cnt} | {b/60:.1f} | {a/60:.1f} |")
    L += ["", "## Sensitivity — hours saved per quarter",
          "| Hand-off rate ↓ · check minutes → | " + " | ".join(f"{m} min" for m in cfg["sensitivity"]["residual_minutes"]) + " |",
          "|---|" + "---:|" * len(cfg["sensitivity"]["residual_minutes"])]
    for er, row in sens.items():
        L.append(f"| {er} | " + " | ".join(f"{v}" for v in row.values()) + " |")
    in_period = [x for x in replay if x["in_period"]]
    L += ["", "## What the chaser did (replay of the period, dry-run)",
          f"{len(events)} messages scheduled: " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())) + ". "
          f"Inside the period: {sum(x['esign_requests'] for x in in_period)} e-sign requests, and — if no form were ever "
          f"returned (worst case) — up to {sum(x['reminders'] for x in in_period)} reminders and "
          f"{sum(x['handoffs'] for x in in_period)} hand-offs; reminders stop as soon as a form comes back, so the expected "
          f"hand-offs are ~{rate*n:.0f} at the assumed {rate:.0%}. Busiest day: "
          f"{max(in_period, key=lambda x: x['esign_requests'] + x['reminders'] + x['handoffs'])['date']}. "
          "Day-by-day log: `replay_by_day.csv`; every message: `outbox.jsonl`; state per request: `tracker.csv`.",
          "", f"## Chase list for {as_of} — steps due today if the form isn't back yet",
          *([f"- {e['request_id']} — {e['type']} → {e['to']}" for e in chase_today] or ["- Nothing due on this date."]),
          "", "## Data quality"]
    L += [f"- Quarantined {b.get('Ticket_ID') or '?'} (line {b['source_line']}): {b['errors']}" for b in bad] or ["- No rows quarantined."]
    L += [f"- {w}" for w in warnings if any(t['ticket'] in w for t in tracker)]
    L += ["- No country field in the log, so the chaser can't pre-pick W-9 vs W-8BEN; the creator selects in the e-sign flow.",
          "- No 'form returned' date in the log, so return rates can't be measured yet; the spec makes logging it step 1."]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickets", default=str(ROOT / "support_tickets_q1_2026.csv"))
    ap.add_argument("--config", default=str(HERE / "taxform_config.json"))
    ap.add_argument("--out", default=str(A / "output" / "taxform"))
    ap.add_argument("--as-of", default=None, help="tracker date (default: last ticket date)")
    a = ap.parse_args()
    s = run(Path(a.tickets), json.loads(Path(a.config).read_text(encoding="utf-8")), Path(a.out),
            date.fromisoformat(a.as_of) if a.as_of else None)
    print(json.dumps({k: v for k, v in s.items() if k != "sensitivity_saved_hours"}, indent=2))
    print(f"report: {Path(a.out) / 'report.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
