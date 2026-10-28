#!/usr/bin/env python3
"""Build Analysis/output/Sales_hiring_raw_data.xlsx — every Sales-hiring statement, verbatim, with source line.
Usage: python Analysis/build_sales_workbook.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

A = Path(__file__).resolve().parent
ROOT = A.parent
sys.path.insert(0, str(A))
from nwlib.sources import load_doc, load_notes, load_slack  # noqa: E402

F = "Arial"
H_FONT = Font(name=F, bold=True, color="FFFFFF")
H_FILL = PatternFill("solid", fgColor="1F3864")
BASE = Font(name=F, size=10)
BOLD = Font(name=F, size=10, bold=True)
RED_FILL = PatternFill("solid", fgColor="F8CBAD")      # conflict / superseded
AMBER_FILL = PatternFill("solid", fgColor="FFE699")    # open / unverified
GREEN_FILL = PatternFill("solid", fgColor="C6EFCE")    # decision
GREY_FILL = PatternFill("solid", fgColor="EDEDED")     # context
THIN = Border(bottom=Side(style="thin", color="BFBFBF"))
WRAP = Alignment(wrap_text=True, vertical="top")
SLACK, NOTES, ROSTER = "slack_export.md", "meeting_notes/leadership_sync_2026-06-11.md", "headcount_roster.csv"

# (file, line, stance, decision?, flag, commentary)
ROWS = [
    (SLACK, 17, "HIRE", "", "", "Tomás pushes to seat an AE on REQ-114 by mid-July. Advocacy, not a decision."),
    (SLACK, 20, "DEFER", "", "", "Marcus (COO): wait for Q2 pipeline before adding headcount."),
    (SLACK, 23, "HIRE", "", "", "Tomás: conversion is partly a coverage problem. Argument for hiring."),
    (SLACK, 26, "DEFER", "", "", "Dana parks the headcount question until after the board deck. No decision yet."),
    (ROSTER, 2, "context", "", "", "Snapshot date for the roster. Everything in the roster reflects 2026-05-01."),
    (ROSTER, 22, "HIRE", "", "SUPERSEDED",
     "REQ-114 shows APPROVED with a 2026-07-15 start. Superseded by the 2026-06-10 freeze: Elena calls the roster "
     "'now stale' (slack L230) and the minutes say 'superseded by this decision' (leadership_sync L16). Conflict C1."),
    (SLACK, 222, "HIRE", "", "SUPERSEDED", "Elena confirms the May 1 snapshot lists REQ-114 as approved. Superseded on Jun 10–11 (C1)."),
    (SLACK, 225, "HIRE", "", "", "Tomás: needs the AE seated by July 15."),
    (SLACK, 67, "FREEZE", "Yes", "DECISION",
     "THE DECISION. CEO freezes all new Sales headcount, REQ-114 included; Priya holds the line on reqs. "
     "Dated Wed Jun 10. The minutes record the same decision dated Jun 11 (C2)."),
    (SLACK, 70, "FREEZE", "", "", "Enforcer confirms: REQ-114 'paused, not killed'. Revisit 'when Q2 pipeline shows recovery' (C3)."),
    (SLACK, 73, "FREEZE", "", "", "Tomás objects on record but complies. Dissent, not a reversal."),
    (SLACK, 76, "FREEZE", "", "", "COO backs it; revisit 'at the Q2 review'. The minutes say July sync with a specific trigger (C3)."),
    (SLACK, 79, "FREEZE", "Yes", "DECISION",
     "Ownership stated explicitly: 'I'm making the call, Priya enforces it'. Freeze is Sales-only."),
    (NOTES, 15, "context", "", "", "Question put to the room: keep hiring into Sales or hold? Framing, not a stance."),
    (NOTES, 16, "FREEZE", "Yes", "DECISION",
     "Formal minute of the decision; states the 05-01 roster is superseded. File and header date it 2026-06-11, "
     "but Slack has it Jun 10 and Elena on Jun 11 says 'yesterday's leadership call' (C2)."),
    (NOTES, 17, "FREEZE", "", "SCOPE",
     "Scope: net-new Sales reqs only; backfills reviewed case by case by Priya + Tomás. Slack says 'all new Sales headcount' "
     "and doesn't mention backfills (C4)."),
    (NOTES, 18, "FREEZE", "Yes", "DECISION", "Owner: Dana (CEO). Enforcer: Priya (CFO). Matches slack L67, L79."),
    (NOTES, 19, "FREEZE", "", "", "Revisit trigger: pipeline coverage on target + 2 months recovered conversion; re-evaluate at July sync (C3)."),
    (NOTES, 20, "context", "", "OPEN",
     "Late-stage REQ-114 candidate: pause, or finish the loop without an offer? Priya + Tomás to align. Outcome not in the bundle."),
    (NOTES, 21, "context", "", "OPEN", "Recruiting to pause the req in Greenhouse; Marcus to notify Elena. Completion not in the bundle."),
    (SLACK, 230, "FREEZE", "", "", "People confirms the freeze and says the May 1 roster is stale (C1); also dates the call to the previous day (C2)."),
    (SLACK, 233, "context", "", "", "Sofia asks whether the freeze covers the Creator Management backfill."),
    (SLACK, 236, "FREEZE", "", "", "Freeze is Sales-only; other teams' open reqs unaffected."),
    (SLACK, 244, "FREEZE", "", "", "Q3 planning: don't submit Sales reqs while the freeze holds. Latest statement in the bundle; still frozen."),
]

CONFLICTS = [
    ("C1", "REQ-114 status", "headcount_roster.csv L22 — APPROVED, start 2026-07-15 (snapshot 2026-05-01)",
     "slack L67, L70, L230; leadership_sync L16 — frozen / paused / roster superseded",
     "Later, explicit sources win. Roster is a stale snapshot.", "Status = PAUSED, not approved", "High",
     "Update the roster / Greenhouse (Elena)"),
    ("C2", "Decision date", "slack L67 — Wed 2026-06-10 08:47",
     "leadership_sync file/header — Thu 2026-06-11; Elena on Jun 11 (L230): 'yesterday's leadership call'",
     "2026-06-10. Minutes appear written up the next day.", "None on the state; date only", "High", "—"),
    ("C3", "When the freeze is revisited", "slack L76 (Marcus) — 'at the Q2 review'; L70 (Priya) — 'when Q2 pipeline shows recovery'",
     "leadership_sync L19 — July sync; trigger = coverage on target + 2 months recovered conversion",
     "Minutes are the most specific; the others are compatible.", "Defines when it could lift", "Medium",
     "July leadership notes"),
    ("C5", "Which non-Sales roles are open?", "headcount_roster.csv L23–L25 — REQ-118 (Eng), REQ-121 (Content), REQ-125 (Data)",
     "slack L222 (Elena, May 1, 'official picture') — Sales AE, Creator Mgmt backfill, one Eng role",
     "Neither list is complete. Union = 4 open non-Sales roles (5+ if Eng has 'a couple', L217).", "Open-role count 4–5+", "Medium",
     "Greenhouse export / updated req list (Elena)"),
    ("C4", "Do backfills count?", "slack L67 — 'all new Sales headcount'",
     "leadership_sync L17 — net-new only; backfills case by case (Priya + Tomás)",
     "Minutes add detail. Net-new frozen; backfills need sign-off.", "Scope of the freeze", "Medium",
     "Confirm with Priya"),
]

# Other (non-Sales) roles: (role, req, team, manager, status, start, in_roster, in_people_may1, raw_src, flag, commentary)
OTHER = [
    ("Backend Engineer", "REQ-118", "Engineering", "Raj Patel", "OPEN", "2026-08-01", "Yes (L23)", "Yes — 'an Eng role' (slack L222)",
     (ROSTER, 23), "CHECK", "Raj: Eng has 'a couple open but no urgency' (slack L217), but the roster lists only one Eng req."),
    ("Senior Video Editor", "REQ-121", "Content/Production", "Yuki Tanaka", "OPEN", "2026-07-01", "Yes (L24)", "No",
     (ROSTER, 24), "CONFLICT", "In the roster but missing from Elena's May 1 'official picture' (slack L222)."),
    ("Analytics Engineer", "REQ-125", "Data", "Ben Okoro", "OPEN", "", "Yes (L25)", "No",
     (ROSTER, 25), "CONFLICT", "No target start date (roster L25), so urgency can't be judged. Also missing from Elena's May 1 list (slack L222)."),
    ("Creator Management backfill", "— (no req ID)", "Creator Management", "Sofia Marchetti", "Open — proceeding", "", "No", "Yes (slack L222)",
     (SLACK, 239), "CONFLICT", "Not in the roster at all. Sofia: 'one backfill open' (L214); confirmed unaffected by the freeze and proceeding (L236, L239)."),
    ("Lifecycle marketer", "— (proposed)", "Growth/Marketing", "Hannah Cole", "Proposed for Q3", "", "No", "No",
     (SLACK, 247), "PROPOSED", "Not a req yet. Hannah 'will write it up' for Q3 planning; requests due end of June (slack L243)."),
    ("Post-production video editor", "— (proposed)", "Content/Production", "Yuki Tanaka", "Proposed for Q3", "", "No", "No",
     (SLACK, 250), "PROPOSED", "Yuki 'will submit'; post is the real bottleneck (also L34). Unclear if additional to REQ-121 or overlapping."),
]

ACTIONS = [
    (NOTES, 42, "Confirm REQ-114 candidate handling (pause vs finish loop, no offer)", "Priya + Tomás", "2026-06-13",
     "Not evidenced", "Risk: an offer goes out against a frozen req."),
    (NOTES, 43, "Notify Elena/People to pause Sales req in Greenhouse", "Marcus", "2026-06-12",
     "Partly evidenced", "Elena knew on Jun 11 (slack L230), but the Greenhouse status isn't in the bundle."),
    (NOTES, 19, "Re-evaluate freeze at July leadership sync", "Leadership", "July 2026",
     "Not evidenced", "Bundle ends 2026-06-17."),
]


def note(cell, text):
    c = Comment(text, "Analysis")
    c.width, c.height = 380, 150
    cell.comment = c


def header(ws, row, cols, widths):
    for i, (c, w) in enumerate(zip(cols, widths), 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font, cell.fill, cell.alignment = H_FONT, H_FILL, Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row=row + 1, column=1)


def main() -> Path:
    msgs = {(m.cite.file, m.cite.line): m for m in load_slack(ROOT) + load_notes(ROOT)}
    docs = {f: load_doc(ROOT, ROOT / f) for f in (SLACK, NOTES, ROSTER)}
    wb = Workbook()

    # ---------------------------------------------------------------- Timeline
    tl = wb.create_sheet("Timeline (raw)")
    tl["A1"] = ("Every Sales-hiring statement in the bundle, in date order. 'Raw text' is copied verbatim from the "
                "source line. Stance and commentary are my reading.")
    tl["A1"].font = BOLD
    header(tl, 2, ["#", "Date / time", "Source file", "Line", "Who", "Channel / doc", "Raw text (verbatim)",
                   "Stance", "Decision?", "Flag", "Commentary & references"],
           [4, 16, 30, 6, 16, 18, 70, 10, 9, 12, 70])

    def when_of(f, ln):
        m = msgs.get((f, ln))
        if m:
            return m.when, m.who, m.channel
        if f == ROSTER:
            return datetime(2026, 5, 1), "Elena Novak (prepared by)", "Headcount roster"
        return None, "", ""

    rows = []
    for f, ln, st, dec, flag, com in ROWS:
        w, who, ch = when_of(f, ln)
        if f == NOTES:
            who = "Minutes (Marcus)"
            ch = "Leadership sync"
        rows.append((w, f, ln, who, ch, docs[f].line(ln).strip(), st, dec, flag, com))
    rows.sort(key=lambda r: (r[0], r[1] != SLACK, r[2]))
    for i, r in enumerate(rows, 1):
        rr = i + 2
        vals = [i, *r]
        for j, v in enumerate(vals, 1):
            c = tl.cell(row=rr, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        tl.cell(row=rr, column=2).number_format = "yyyy-mm-dd hh:mm" if (r[0].hour or r[0].minute) else "yyyy-mm-dd"
        if not (r[0].hour or r[0].minute):
            note(tl.cell(row=rr, column=2), "No timestamp in the source — date only (minutes: file date; roster: snapshot date).")
        flag = r[8]
        fill = {"DECISION": GREEN_FILL, "SUPERSEDED": RED_FILL, "SCOPE": AMBER_FILL, "OPEN": AMBER_FILL}.get(flag)
        if r[6] == "context" and not flag:
            fill = GREY_FILL
        if fill:
            for j in (7, 8, 10):
                tl.cell(row=rr, column=j).fill = fill
        if flag in ("SUPERSEDED", "DECISION", "SCOPE", "OPEN"):
            tl.cell(row=rr, column=10).font = BOLD
            note(tl.cell(row=rr, column=7), r[9])
    last = len(rows) + 2

    # ---------------------------------------------------------------- Roster raw
    ro = wb.create_sheet("Roster reqs (raw)")
    ro["A1"] = "headcount_roster.csv — header and OPEN_REQUISITIONS section, verbatim (lines 1–4, 20–25)."
    ro["A1"].font = BOLD
    header(ro, 2, ["Line", "Raw row", "Flag", "Commentary & references"], [6, 70, 12, 80])
    r = 3
    for ln in [1, 2, 3, 4, 20, 21, 22, 23, 24, 25]:
        raw = docs[ROSTER].line(ln)
        ro.cell(row=r, column=1, value=ln).font = BASE
        c = ro.cell(row=r, column=2, value=raw)
        c.font, c.alignment = BASE, WRAP
        if ln == 22:
            ro.cell(row=r, column=3, value="SUPERSEDED").font = BOLD
            txt = ("REQ-114 APPROVED as of 2026-05-01. Frozen/paused since 2026-06-10: slack L67 (Dana), L70 (Priya), "
                   "L230 (Elena: 'May 1 roster is now stale'), leadership_sync L16 ('superseded by this decision').")
            ro.cell(row=r, column=4, value=txt).font = BASE
            ro.cell(row=r, column=4).alignment = WRAP
            for j in (2, 3):
                ro.cell(row=r, column=j).fill = RED_FILL
            note(c, txt)
        if ln in (23, 24, 25):
            ro.cell(row=r, column=4, value="Not Sales; freeze is Sales-only (slack L79, L236), so unaffected.").font = BASE
        r += 1
    ro.cell(row=r + 1, column=1, value="Also not in the roster: the Creator Management backfill Elena mentions on May 1 "
                                      "(slack L222). The roster isn't the full req picture.").font = Font(name=F, size=9, italic=True)

    # ---------------------------------------------------------------- Conflicts
    cf = wb.create_sheet("Conflicts")
    cf["A1"] = "Where sources disagree — what each says, how I resolved it, and what it changes."
    cf["A1"].font = BOLD
    header(cf, 2, ["ID", "Issue", "Source A", "Source B", "Resolution", "Effect on answer", "Confidence", "Unblocker"],
           [6, 22, 44, 48, 40, 26, 11, 28])
    for i, row in enumerate(sorted(CONFLICTS), 3):
        for j, v in enumerate(row, 1):
            c = cf.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN

    # ---------------------------------------------------------------- Other open roles
    orl = wb.create_sheet("Other open roles", 2)
    orl["A1"] = ("Non-Sales roles. The freeze is Sales-only ('Other teams' open reqs are unaffected' — slack L79, L236), "
                 "so these stay open. Roster and People's list don't agree — see Flag and Conflict C5.")
    orl["A1"].font = BOLD
    header(orl, 2, ["Role", "Req ID", "Team", "Hiring manager", "Status", "Target start", "Affected by Sales freeze?",
                    "In roster (May 1)?", "In People's May 1 list?", "Raw source (verbatim)", "Source", "Flag", "Commentary & references"],
           [24, 14, 18, 15, 16, 11, 12, 11, 18, 52, 22, 11, 60])
    for i, (role, req, team, mgr, st, start, in_r, in_p, (f, ln), flag, com) in enumerate(OTHER, 3):
        vals = [role, req, team, mgr, st, start or "— (blank)", "No", in_r, in_p, docs[f].line(ln).strip(), f"{f}:L{ln}", flag, com]
        for j, v in enumerate(vals, 1):
            c = orl.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        fill = {"CONFLICT": RED_FILL, "CHECK": AMBER_FILL, "PROPOSED": GREY_FILL}.get(flag)
        if fill:
            for j in (1, 12):
                orl.cell(row=i, column=j).fill = fill
        orl.cell(row=i, column=12).font = BOLD
        if flag in ("CONFLICT", "CHECK"):
            note(orl.cell(row=i, column=1), com)
        if not start:
            orl.cell(row=i, column=6).fill = AMBER_FILL if req.startswith("REQ") else PatternFill()
    n_other = len(OTHER) + 2
    r0 = n_other + 2
    O = lambda col: f"${col}$3:${col}${n_other}"  # noqa: E731
    summ = [("Open non-Sales roles (roster + People list, excl. proposed)", f'=COUNTIFS({O("E")},"OPEN")+COUNTIFS({O("E")},"Open*proceeding")'),
            ("…of which in the roster", f'=COUNTIFS({O("H")},"Yes*")'),
            ("…of which in People's May 1 list", f'=COUNTIFS({O("I")},"Yes*")'),
            ("Proposed for Q3 (not yet reqs)", f'=COUNTIFS({O("E")},"Proposed*")'),
            ("Affected by the Sales freeze", f'=COUNTIFS({O("G")},"Yes")')]
    for k, (lab, f_) in enumerate(summ):
        orl.cell(row=r0 + k, column=1, value=lab).font = BOLD
        c = orl.cell(row=r0 + k, column=2, value=f_)
        c.font = BOLD
    orl.cell(row=r0 + len(summ) + 1, column=1, value=(
        "Bounds: 4 open non-Sales roles in the union of both sources; 5+ if Engineering really has 'a couple' open (slack L217). "
        "Unblock with a Greenhouse export or an updated req list from Elena.")).font = Font(name=F, size=9, italic=True)

    # ---------------------------------------------------------------- Open actions
    oa = wb.create_sheet("Open actions")
    oa["A1"] = "Follow-ups assigned with the decision. Status is what the bundle shows, not what probably happened."
    oa["A1"].font = BOLD
    header(oa, 2, ["Source", "Line", "Action (verbatim from minutes)", "Owner", "Due", "Status in bundle", "Why it matters"],
           [34, 6, 50, 16, 12, 16, 50])
    for i, row in enumerate(ACTIONS, 3):
        for j, v in enumerate(row, 1):
            c = oa.cell(row=i, column=j, value=v)
            c.font, c.alignment, c.border = BASE, WRAP, THIN
        oa.cell(row=i, column=6).fill = AMBER_FILL

    # ---------------------------------------------------------------- Summary
    s = wb.active
    s.title = "Summary"
    for col, w in zip("ABC", (46, 24, 90)):
        s.column_dimensions[col].width = w
    s["A1"] = "Q2 — Sales hiring: hire or freeze? Current state and owner"
    s["A1"].font = Font(name=F, size=14, bold=True)
    s["A2"] = "Counts and dates are live formulas on the 'Timeline (raw)' tab. Text answers cite the source rows."
    s["A2"].font = Font(name=F, size=9, italic=True)
    T = lambda col: f"'Timeline (raw)'!${col}$3:${col}${last}"  # noqa: E731
    items = [
        ("Current state", "FROZEN", BOLD, "slack L67, L79; leadership_sync L16. REQ-114 paused, not cancelled (slack L70)."),
        ("Decision owner", "Dana Whitfield (CEO)", BOLD, "'I'm making the call' (slack L79); 'Decision made by Dana' (leadership_sync L18)."),
        ("Enforcer on reqs", "Priya Raman (CFO)", BOLD, "'Priya holds the line on reqs' (slack L67); 'Priya enforces' (L79, leadership_sync L18)."),
        ("Decision date (first decision statement)",
         f'=_xlfn.MINIFS({T("B")},{T("I")},"Yes",{T("H")},"FREEZE")', BASE,
         "Earliest FREEZE row marked Decision = Yes. Minutes are dated a day later (Conflict C2)."),
        ("Statements found (all stances)", f'=COUNTA({T("H")})', BASE, "Every Sales-hiring line in Slack, minutes and roster."),
        ("FREEZE statements on/after decision", f'=COUNTIFS({T("H")},"FREEZE",{T("B")},">="&B7)', BASE, "Dana, Priya, Marcus, Tomás, Elena + minutes."),
        ("HIRE statements after decision (reversals)", f'=COUNTIFS({T("H")},"HIRE",{T("B")},">"&B7)', BASE, "0 = nothing in the bundle reverses the freeze."),
        ("Reversed since?", '=IF(B10=0,"No — still frozen at end of bundle","Yes — check rows")', BOLD, ""),
        ("Latest Sales-hiring statement", f'=MAX({T("B")})', BASE, "Bundle export range ends 2026-06-17 (slack L4)."),
        ("Revisit", "July leadership sync", BASE,
         "Trigger: pipeline coverage on target + 2 months recovered conversion (leadership_sync L19). Other wording in C3."),
        ("Confidence — state & owner", "High", BOLD, "4 independent sources agree (Dana, Priya, Elena, minutes); no later reversal."),
        ("Other teams' open roles", "Unaffected — see 'Other open roles'", BASE,
         "4 open non-Sales roles (roster and People's list disagree — Conflict C5); 2 more proposed for Q3."),
        ("Confidence — follow-through", "Medium", BOLD, "Candidate handling and Greenhouse pause not evidenced — see 'Open actions'."),
    ]
    for i, (label, val, font, src) in enumerate(items, 4):
        s.cell(row=i, column=1, value=label).font = BASE
        c = s.cell(row=i, column=2, value=val)
        c.font = font
        s.cell(row=i, column=3, value=src).font = BASE
        s.cell(row=i, column=3).alignment = WRAP
    s["B7"].number_format = "yyyy-mm-dd hh:mm"
    s["B12"].number_format = "yyyy-mm-dd hh:mm"
    s["A19"] = "Colour key on 'Timeline (raw)': green = decision · red = superseded / conflicts with the decision · amber = scope note or open item · grey = context."
    s["A19"].font = Font(name=F, size=9, italic=True)
    s["A20"] = "Scope: Sales headcount decisions, 2026-04-21 → 2026-06-17 (full bundle). Anything after the last message is unknown."
    s["A20"].font = Font(name=F, size=9, italic=True)

    out = A / "output" / "Sales_hiring_raw_data.xlsx"
    wb.save(out)
    print(out)
    return out


if __name__ == "__main__":
    main()
