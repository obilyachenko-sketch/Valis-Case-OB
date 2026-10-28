#!/usr/bin/env python3
"""Creator-support autopilot — deflects repetitive tickets to self-serve / e-sign flows.

Pipeline (runs end-to-end on support_tickets_q1_2026.csv or any file with the same columns):
  1. ingest + validate against the data contract  -> bad rows go to quarantine.csv (never silently dropped)
  2. route each ticket by Category via playbooks.json
  3. generate the automated action for each deflected ticket -> outbox.jsonl (dry-run: nothing is sent)
  4. compute BEFORE (measured Handle_Minutes) vs AFTER (modelled) -> report.md + ticket_decisions.csv

Usage:
    python Analysis/automation/support_autopilot.py                         # bundle tickets
    python Analysis/automation/support_autopilot.py --tickets new.csv --out DIR
Standard library only.
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
sys.path.insert(0, str(HERE.parent))
from nwlib.sources import read_text  # noqa: E402

REQUIRED = ["Ticket_ID", "Date", "Category", "Submitted_By", "Assigned_To", "Handle_Minutes", "Status"]
STATUSES = {"Open", "Closed"}


# ------------------------------------------------------------------ 1. ingest + validate

def load(path: Path) -> tuple[list[dict], list[dict], list[str]]:
    text, _ = read_text(path)
    rows = list(csv.DictReader(text.replace("\r\n", "\n").splitlines()))
    if not rows:
        raise SystemExit(f"{path}: no rows")
    missing = [c for c in REQUIRED if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: data contract violated, missing columns {missing}")
    good, bad, warnings = [], [], []
    seen: set[str] = set()
    for i, r in enumerate(rows, 2):
        r = {k: (v or "").strip() for k, v in r.items() if k}
        r["source_line"] = i
        errs = []
        if not re.fullmatch(r"TCK-\d+", r["Ticket_ID"]):
            errs.append("bad Ticket_ID")
        elif r["Ticket_ID"] in seen:
            errs.append("duplicate Ticket_ID")
        try:
            date.fromisoformat(r["Date"])
        except ValueError:
            errs.append("bad Date")
        if not r["Category"]:
            errs.append("blank Category")
        try:
            m = int(float(r["Handle_Minutes"]))
            if not 1 <= m <= 480:
                errs.append("Handle_Minutes out of 1-480")
            r["Handle_Minutes"] = m
        except ValueError:
            errs.append("non-numeric Handle_Minutes")
        if r["Status"] not in STATUSES:
            errs.append("unknown Status")
        if errs:
            r["errors"] = "; ".join(errs)
            bad.append(r)
            continue
        seen.add(r["Ticket_ID"])
        if not r["Assigned_To"]:
            warnings.append(f"{r['Ticket_ID']} (line {i}): blank Assigned_To — kept; effort is still logged")
        good.append(r)
    return good, bad, warnings


# ------------------------------------------------------------------ 2+3. route + act

def act(r: dict, pb: dict) -> list[dict]:
    """Build the outbound actions for one deflected ticket (dry-run payloads)."""
    d = date.fromisoformat(r["Date"])
    who = r["Submitted_By"]
    if pb["action"] == "SELF_SERVE_THUMBNAIL":
        return [{"ticket": r["Ticket_ID"], "type": "SELF_SERVE_THUMBNAIL", "to": who, "send_on": d.isoformat(),
                 "template": "thumbnail_self_serve_v1",
                 "body": f"Hi @{who} — you can replace your thumbnail yourself here; it goes live within minutes. "
                         f"Reply to this message if it doesn't work and a person will pick it up. "
                         f"[self-serve link for {r['Ticket_ID']}]"}]
    if pb["action"] == "ESIGN_TAX_FORM":
        acts = [{"ticket": r["Ticket_ID"], "type": "ESIGN_REQUEST", "to": who, "send_on": d.isoformat(),
                 "template": "tax_form_esign_v1",
                 "body": f"Hi @{who} — please complete your tax form (W-9 if US, W-8BEN if not) via this secure "
                         f"e-sign link. Takes about 3 minutes. [e-sign link for {r['Ticket_ID']}]"}]
        for n in pb.get("reminder_days", []):
            acts.append({"ticket": r["Ticket_ID"], "type": "ESIGN_REMINDER", "to": who,
                         "send_on": (d + timedelta(days=n)).isoformat(), "template": "tax_form_reminder_v1",
                         "condition": "only if form not yet returned"})
        acts.append({"ticket": r["Ticket_ID"], "type": "ESCALATE_TO_HUMAN", "to": "Ops Support",
                     "send_on": (d + timedelta(days=pb.get("escalate_after_days", 21))).isoformat(),
                     "condition": "only if form still not returned"})
        return acts
    raise ValueError(pb["action"])


def run(tickets: Path, cfg: dict, out: Path) -> dict:
    good, bad, warnings = load(tickets)
    pbs, f = cfg["playbooks"], float(cfg["fallback_rate"])
    out.mkdir(parents=True, exist_ok=True)

    decisions, outbox = [], []
    for r in good:
        pb = pbs.get(r["Category"])
        before = r["Handle_Minutes"]
        if pb:
            after = (1 - f) * pb["residual_minutes"] + f * before
            acts = act(r, pb)
            outbox += acts
            route = pb["action"]
        else:
            after, route, acts = float(before), "HUMAN", []
        decisions.append({"Ticket_ID": r["Ticket_ID"], "source_line": r["source_line"], "Date": r["Date"],
                          "Category": r["Category"], "route": route, "actions": len(acts),
                          "before_min": before, "after_min": round(after, 2)})

    with open(out / "ticket_decisions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(decisions[0]))
        w.writeheader()
        w.writerows(decisions)
    with open(out / "outbox.jsonl", "w", encoding="utf-8") as fh:
        for a in outbox:
            fh.write(json.dumps(a, ensure_ascii=False) + "\n")
    with open(out / "quarantine.csv", "w", newline="", encoding="utf-8") as fh:
        cols = REQUIRED + ["source_line", "errors"]
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(bad)

    # ------------------------------------------------------------ 4. before -> after
    dates = [date.fromisoformat(d["Date"]) for d in decisions]
    weeks = ((max(dates) - min(dates)).days + 1) / 7
    by_cat = defaultdict(lambda: [0, 0.0, 0.0, ""])
    for d in decisions:
        c = by_cat[d["Category"]]
        c[0] += 1
        c[1] += d["before_min"]
        c[2] += d["after_min"]
        c[3] = d["route"]
    before = sum(d["before_min"] for d in decisions)
    after = sum(d["after_min"] for d in decisions)
    defl = [d for d in decisions if d["route"] != "HUMAN"]

    def after_for(fr: float, res_scale: float = 1.0) -> float:
        tot = 0.0
        for d in decisions:
            pb = pbs.get(d["Category"])
            tot += ((1 - fr) * pb["residual_minutes"] * res_scale + fr * d["before_min"]) if pb else d["before_min"]
        return tot

    summary = {
        "input_rows": len(good) + len(bad), "processed": len(good), "quarantined": len(bad),
        "warnings": warnings, "weeks_covered": round(weeks, 2),
        "before_minutes": before, "after_minutes": round(after, 1),
        "before_hours": round(before / 60, 1), "after_hours": round(after / 60, 1),
        "saved_hours": round((before - after) / 60, 1),
        "saved_pct": round(100 * (before - after) / before, 1),
        "before_hours_per_week": round(before / 60 / weeks, 2),
        "after_hours_per_week": round(after / 60 / weeks, 2),
        "tickets_deflected": len(defl), "actions_generated": len(outbox),
        "human_touches_before": len(decisions),
        "human_touches_after_expected": round(len(decisions) - len(defl) + f * len(defl), 1),
        "fallback_rate": f,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    L = [f"# Support autopilot — run report\n",
         f"Input: `{tickets.name}` · {summary['input_rows']} rows · {summary['processed']} processed · "
         f"{summary['quarantined']} quarantined · period {min(dates)} → {max(dates)} ({weeks:.1f} weeks)\n",
         "## Before → after",
         "| | Before (measured) | After (modelled) | Change |", "|---|---:|---:|---:|",
         f"| Handle time, quarter | {before/60:.1f} h | {after/60:.1f} h | **−{(before-after)/60:.1f} h (−{summary['saved_pct']}%)** |",
         f"| Handle time per week | {before/60/weeks:.2f} h | {after/60/weeks:.2f} h | −{(before-after)/60/weeks:.2f} h |",
         f"| Tickets needing a person | {len(decisions)} | {summary['human_touches_after_expected']} (expected) | "
         f"−{len(decisions)-summary['human_touches_after_expected']:.1f} |",
         "", "**Before** = sum of `Handle_Minutes` on every processed row (measured). "
         f"**After** = deflected tickets cost `residual_minutes` when the flow works, and full original minutes for the "
         f"{f:.0%} that fall back to a person; everything else unchanged (modelled — see assumptions).\n",
         "## By category",
         "| Category | Tickets | Route | Before h | After h | Saved h |", "|---|---:|---|---:|---:|---:|"]
    for k, (n, b, a, route) in sorted(by_cat.items(), key=lambda x: -x[1][1]):
        L.append(f"| {k} | {n} | {route} | {b/60:.1f} | {a/60:.1f} | {(b-a)/60:.1f} |")
    L += ["", "## Assumptions (not measurable from the bundle) and sensitivity",
          f"- Fallback rate (deflected ticket still needs a person, full original minutes): **{f:.0%}**",
          *[f"- {k}: residual **{v['residual_minutes']} min** per deflected ticket — {v['why']}" for k, v in pbs.items()],
          "", "| Fallback rate → | " + " | ".join(f"{x:.0%}" for x in (0.1, 0.2, 0.3, 0.5)) + " |",
          "|---|" + "---:|" * 4]
    for scale, label in ((1.0, "residual as configured"), (2.0, "residual ×2")):
        L.append(f"| Saved h / quarter ({label}) | " +
                 " | ".join(f"{(before - after_for(x, scale))/60:.1f}" for x in (0.1, 0.2, 0.3, 0.5)) + " |")
    L += ["", "## Actions generated (dry-run outbox)",
          f"{len(outbox)} actions for {len(defl)} tickets → `outbox.jsonl` "
          f"({', '.join(f'{k}: {v}' for k, v in Counter(a['type'] for a in outbox).items())}). Nothing is sent; a "
          "builder wires these to the CMS self-serve endpoint and an e-sign provider.",
          "", "## Data quality"]
    L += [f"- Quarantined: {b['Ticket_ID'] or '?'} (line {b['source_line']}): {b['errors']}" for b in bad] or ["- No rows quarantined."]
    L += [f"- Warning: {w}" for w in warnings]
    L += ["", "## Out of scope (kept with a person)"] + [f"- {k}: {v}" for k, v in cfg.get("out_of_scope", {}).items()]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    root = HERE.parent.parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickets", default=str(root / "support_tickets_q1_2026.csv"))
    ap.add_argument("--config", default=str(HERE / "playbooks.json"))
    ap.add_argument("--out", default=str(HERE.parent / "output" / "autopilot"))
    a = ap.parse_args()
    s = run(Path(a.tickets), json.loads(Path(a.config).read_text(encoding="utf-8")), Path(a.out))
    print(json.dumps({k: v for k, v in s.items() if k != "warnings"}, indent=2))
    print(f"report: {Path(a.out) / 'report.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
