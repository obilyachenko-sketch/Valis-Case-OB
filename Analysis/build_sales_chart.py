#!/usr/bin/env python3
"""Build Analysis/output/sales_hiring_timeline.html from the same rows as the Sales workbook.
Usage: python Analysis/build_sales_chart.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

A = Path(__file__).resolve().parent
sys.path.insert(0, str(A))
import build_sales_workbook as bw  # noqa: E402
from nwlib.sources import load_doc, load_notes, load_slack  # noqa: E402

LABELS = {  # selective direct labels (key moments only)
    (bw.SLACK, 17): "Tomás pushes to seat an AE (REQ-114)",
    (bw.SLACK, 26): "Dana: “Park it”",
    (bw.ROSTER, 22): "Roster: REQ-114 APPROVED (superseded)",
    (bw.SLACK, 67): "Dana: FREEZE all new Sales headcount",
    (bw.NOTES, 16): "Minutes record DECISION",
    (bw.SLACK, 244): "Elena: no Sales reqs for Q3",
}


def main() -> Path:
    root = bw.ROOT
    msgs = {(m.cite.file, m.cite.line): m for m in load_slack(root) + load_notes(root)}
    docs = {f: load_doc(root, root / f) for f in (bw.SLACK, bw.NOTES, bw.ROSTER)}
    data = []
    for f, ln, st, dec, flag, com in bw.ROWS:
        if f == bw.ROSTER and ln == 2:
            continue  # snapshot-date header row, not a statement
        m = msgs.get((f, ln))
        if m:
            when, who = m.when, m.who
        elif f == bw.ROSTER:
            when, who = datetime(2026, 5, 1), "Headcount roster"
        if f == bw.NOTES:
            who = "Leadership minutes"
        data.append({"t": when.strftime("%Y-%m-%dT%H:%M"), "timed": bool(when.hour or when.minute),
                     "file": f, "line": ln, "who": who, "stance": st, "decision": dec == "Yes", "flag": flag,
                     "text": docs[f].line(ln).strip().lstrip("- ").replace("**", ""), "note": com,
                     "label": LABELS.get((f, ln), "")})
    tpl = (A / "templates" / "sales_timeline_template.html").read_text(encoding="utf-8")
    out = A / "output" / "sales_hiring_timeline.html"
    out.write_text(tpl.replace("/*DATA*/[]", json.dumps(data, ensure_ascii=False)), encoding="utf-8")
    print(out, len(data), "points")
    return out


if __name__ == "__main__":
    main()
